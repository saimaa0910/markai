"""Device Trust Routes — Sprint 8.3.1 Phase 4

API endpoints for trusted device management.
"""
import uuid
import logging
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user
from api.models.user import User
from api.models.security import TrustedDevice


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/devices", tags=["device-trust"])


# Request/Response Models

class TrustDeviceRequest(BaseModel):
    """Request to trust a device."""
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    duration_days: Optional[int] = Field(None, ge=1, le=365, description="Trust duration in days")


class TrustedDeviceResponse(BaseModel):
    """Trusted device information."""
    device_id: str
    trusted: bool = True
    device_name: Optional[str] = None
    device_fingerprint: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    location: Optional[str] = None
    trusted_at: Optional[str] = None
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    is_active: bool = True


class TrustedDevicesListResponse(BaseModel):
    """List of trusted devices."""
    devices: List[TrustedDeviceResponse]
    total: int


def _to_response(device) -> dict:
    return {
        "device_id": str(device.id),
        "trusted": bool(device.is_active),
        "device_name": device.device_name,
        "device_fingerprint": device.device_fingerprint,
        "device_type": device.device_type,
        "browser": device.browser,
        "os": device.os,
        "location": device.location,
        "trusted_at": device.trusted_at.isoformat() if device.trusted_at else None,
        "expires_at": device.expires_at.isoformat() if device.expires_at else None,
        "last_used_at": device.last_used_at.isoformat() if device.last_used_at else None,
        "is_active": bool(device.is_active),
    }


# Endpoints

@router.post("/trust", response_model=TrustedDeviceResponse, status_code=status.HTTP_200_OK)
async def trust_device(
    request: Request,
    body: TrustDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark the current device as trusted."""
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "unknown"

    now = datetime.now(timezone.utc)
    expires_at = None
    if body.duration_days:
        expires_at = now + timedelta(days=body.duration_days)

    device = TrustedDevice(
        user_id=current_user.id,
        device_fingerprint=body.device_fingerprint,
        device_name=body.device_name,
        device_type="desktop",
        browser="Unknown",
        os="Unknown",
        ip_address=ip_address,
        location=None,
        trusted_at=now,
        last_used_at=now,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info(f"User {current_user.id} trusted device {device.id}")
    return TrustedDeviceResponse(**_to_response(device))


@router.get("/trusted", response_model=TrustedDevicesListResponse)
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all trusted devices for the current user."""
    devices = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.user_id == current_user.id, TrustedDevice.is_active == True)
        .order_by(TrustedDevice.trusted_at.desc())
        .all()
    )
    return TrustedDevicesListResponse(
        devices=[TrustedDeviceResponse(**_to_response(d)) for d in devices],
        total=len(devices),
    )


@router.delete("/trusted/all", status_code=status.HTTP_200_OK)
async def revoke_all_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke trust for all devices."""
    now = datetime.now(timezone.utc)
    devices = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.user_id == current_user.id, TrustedDevice.is_active == True)
        .all()
    )
    count = 0
    for device in devices:
        device.is_active = False
        device.revoked_at = now
        device.revoked_by = current_user.id
        device.revoke_reason = "User requested revocation of all devices"
        count += 1
    db.commit()

    logger.info(f"User {current_user.id} revoked all {count} trusted devices")
    return {"message": f"Successfully revoked {count} trusted devices", "revoked_count": count}


@router.delete("/trusted/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke trust for a specific device."""
    device = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.id == device_id, TrustedDevice.user_id == current_user.id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    device.is_active = False
    device.revoked_at = datetime.now(timezone.utc)
    device.revoked_by = current_user.id
    device.revoke_reason = "User requested"
    db.commit()

    logger.info(f"User {current_user.id} revoked device {device_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
