"""Device Trust Routes — Sprint 8.3.1 Phase 4

API endpoints for trusted device management.
"""
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.services.device_trust_service import DeviceTrustService
from api.services.audit_log_service import AuditLogService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/devices", tags=["device-trust"])


# Request/Response Models

class TrustDeviceRequest(BaseModel):
    """Request to trust a device."""
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    duration_days: Optional[int] = Field(None, ge=1, le=365, description="Trust duration in days")


class TrustedDeviceResponse(BaseModel):
    """Trusted device information."""
    id: str
    device_name: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    location: Optional[str]
    trusted_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    is_active: bool


class TrustedDevicesListResponse(BaseModel):
    """List of trusted devices."""
    devices: List[TrustedDeviceResponse]
    total: int


class RevokeDeviceRequest(BaseModel):
    """Request to revoke device trust."""
    reason: Optional[str] = Field(None, description="Reason for revocation")


# Helper Functions

def extract_device_info(request: Request) -> dict:
    """Extract device information from request headers."""
    user_agent = request.headers.get("user-agent", "")
    accept_language = request.headers.get("accept-language", "")
    
    # Simple browser/OS detection (production would use a library like user-agents)
    browser = "Unknown"
    os = "Unknown"
    device_type = "desktop"
    
    if "Mobile" in user_agent or "Android" in user_agent:
        device_type = "mobile"
    elif "Tablet" in user_agent or "iPad" in user_agent:
        device_type = "tablet"
    
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Safari" in user_agent:
        browser = "Safari"
    elif "Edge" in user_agent:
        browser = "Edge"
    
    if "Windows" in user_agent:
        os = "Windows"
    elif "Macintosh" in user_agent or "Mac OS" in user_agent:
        os = "macOS"
    elif "Linux" in user_agent:
        os = "Linux"
    elif "Android" in user_agent:
        os = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        os = "iOS"
    
    # Get IP address
    ip_address = request.client.host if request.client else "unknown"
    
    # For location, you'd typically use a GeoIP service
    location = None  # Would be filled by GeoIP service
    
    return {
        "browser": browser,
        "os": os,
        "device_type": device_type,
        "ip_address": ip_address,
        "location": location,
    }


# Endpoints

@router.post("/trust", response_model=TrustedDeviceResponse, status_code=status.HTTP_201_CREATED)
async def trust_device(
    request: Request,
    body: TrustDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark the current device as trusted.
    
    This allows the user to skip MFA on this device for the specified duration.
    """
    try:
        # Extract device information from request
        device_info = extract_device_info(request)
        
        # Add user-provided device name
        if body.device_name:
            device_info["device_name"] = body.device_name
        
        # Generate device fingerprint
        user_agent = request.headers.get("user-agent", "")
        ip_address = device_info["ip_address"]
        accept_language = request.headers.get("accept-language", "")
        
        device_fingerprint = DeviceTrustService.generate_device_fingerprint(
            user_agent=user_agent,
            ip_address=ip_address,
            accept_language=accept_language,
        )
        
        # Trust the device
        trusted_device = await DeviceTrustService.trust_device(
            db=db,
            user_id=current_user.id,
            device_fingerprint=device_fingerprint,
            device_info=device_info,
            duration_days=body.duration_days,
        )
        
        # Log the action
        await AuditLogService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="device_trusted",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "device_id": trusted_device["id"],
                "device_name": trusted_device.get("device_name"),
                "duration_days": body.duration_days,
            },
        )
        
        logger.info(f"User {current_user.id} trusted device {trusted_device['id']}")
        
        return TrustedDeviceResponse(**trusted_device)
        
    except ValueError as e:
        logger.warning(f"Failed to trust device for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error trusting device for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trust device",
        )


@router.get("/trusted", response_model=TrustedDevicesListResponse)
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all trusted devices for the current user.
    """
    try:
        devices = await DeviceTrustService.list_trusted_devices(
            db=db,
            user_id=current_user.id,
            include_revoked=False,
        )
        
        return TrustedDevicesListResponse(
            devices=[TrustedDeviceResponse(**device) for device in devices],
            total=len(devices),
        )
        
    except Exception as e:
        logger.error(f"Error listing trusted devices for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list trusted devices",
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: uuid.UUID,
    body: Optional[RevokeDeviceRequest] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke trust for a specific device.
    """
    try:
        reason = body.reason if body else "User requested"
        
        await DeviceTrustService.revoke_device(
            db=db,
            user_id=current_user.id,
            device_id=device_id,
            reason=reason,
        )
        
        # Log the action
        ip_address = request.client.host if request and request.client else "unknown"
        user_agent = request.headers.get("user-agent", "") if request else ""
        
        await AuditLogService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="device_revoked",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "device_id": str(device_id),
                "reason": reason,
            },
        )
        
        logger.info(f"User {current_user.id} revoked device {device_id}")
        
    except ValueError as e:
        logger.warning(f"Failed to revoke device {device_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error revoking device {device_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke device",
        )


@router.delete("/all", status_code=status.HTTP_200_OK)
async def revoke_all_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke trust for all devices.
    """
    try:
        count = await DeviceTrustService.revoke_all_devices(
            db=db,
            user_id=current_user.id,
            reason="User requested revocation of all devices",
        )
        
        # Log the action
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        await AuditLogService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="device_revoked",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "action": "revoke_all",
                "devices_revoked": count,
            },
        )
        
        logger.info(f"User {current_user.id} revoked all {count} trusted devices")
        
        return {
            "message": f"Successfully revoked {count} trusted devices",
            "devices_revoked": count,
        }
        
    except Exception as e:
        logger.error(f"Error revoking all devices for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke all devices",
        )
