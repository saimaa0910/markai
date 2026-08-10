"""MFA Recovery Routes — Sprint 8.3.1 Phase 4

API endpoints for MFA recovery code management.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.services.mfa_recovery_service import MFARecoveryService
from api.services.audit_log_service import AuditLogService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/mfa/recovery", tags=["mfa-recovery"])


# Request/Response Models

class GenerateRecoveryCodesResponse(BaseModel):
    """Response with newly generated recovery codes."""
    recovery_codes: List[str] = Field(..., description="10 single-use recovery codes")
    generated_at: str = Field(..., description="Generation timestamp")
    warning: str = Field(
        default="Save these codes securely. They cannot be retrieved again.",
        description="Security warning"
    )


class VerifyRecoveryCodeRequest(BaseModel):
    """Request to verify a recovery code."""
    recovery_code: str = Field(..., description="Recovery code in format XXXX-XXXX-XXXX-XXXX")


class VerifyRecoveryCodeResponse(BaseModel):
    """Response after verifying recovery code."""
    success: bool
    message: str
    remaining_codes: Optional[int] = None


class RecoveryCodesStatusResponse(BaseModel):
    """Recovery codes status information."""
    total: int = Field(..., description="Total codes generated")
    used: int = Field(..., description="Number of used codes")
    remaining: int = Field(..., description="Number of unused codes")
    generated_at: Optional[str] = Field(None, description="When codes were last generated")


# Endpoints

@router.post("/generate", response_model=GenerateRecoveryCodesResponse, status_code=status.HTTP_201_CREATED)
async def generate_recovery_codes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate new MFA recovery codes.
    
    This revokes all existing recovery codes and creates 10 new ones.
    Requires MFA to be enabled.
    """
    try:
        # Generate recovery codes
        recovery_codes = await MFARecoveryService.generate_recovery_codes(
            db=db,
            user_id=current_user.id,
        )
        
        # Log the action
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        await AuditLogService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="mfa_recovery_regenerated",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "codes_generated": len(recovery_codes),
            },
        )
        
        logger.info(f"Generated recovery codes for user {current_user.id}")
        
        from datetime import datetime, timezone
        return GenerateRecoveryCodesResponse(
            recovery_codes=recovery_codes,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        
    except ValueError as e:
        logger.warning(f"Failed to generate recovery codes for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating recovery codes for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recovery codes",
        )


@router.post("/verify", response_model=VerifyRecoveryCodeResponse)
async def verify_recovery_code(
    request: Request,
    body: VerifyRecoveryCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a recovery code during login.
    
    This marks the code as used and cannot be reused.
    """
    try:
        # Get IP address
        ip_address = request.client.host if request.client else "unknown"
        
        # Verify the recovery code
        is_valid = await MFARecoveryService.verify_recovery_code(
            db=db,
            user_id=current_user.id,
            code=body.recovery_code,
            used_from_ip=ip_address,
        )
        
        if is_valid:
            # Get remaining codes count
            status_info = await MFARecoveryService.get_recovery_codes_status(
                db=db,
                user_id=current_user.id,
            )
            
            # Log the action
            user_agent = request.headers.get("user-agent", "")
            
            await AuditLogService.log_event(
                db=db,
                user_id=current_user.id,
                event_type="mfa_recovery_used",
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    "remaining_codes": status_info["remaining"],
                },
            )
            
            logger.info(f"Recovery code verified for user {current_user.id}")
            
            return VerifyRecoveryCodeResponse(
                success=True,
                message="Recovery code verified successfully",
                remaining_codes=status_info["remaining"],
            )
        else:
            logger.warning(f"Invalid recovery code for user {current_user.id}")
            return VerifyRecoveryCodeResponse(
                success=False,
                message="Invalid or already used recovery code",
            )
        
    except Exception as e:
        logger.error(f"Error verifying recovery code for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify recovery code",
        )


@router.get("/status", response_model=RecoveryCodesStatusResponse)
async def get_recovery_codes_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current status of recovery codes.
    
    Shows how many codes are generated, used, and remaining.
    """
    try:
        status_info = await MFARecoveryService.get_recovery_codes_status(
            db=db,
            user_id=current_user.id,
        )
        
        return RecoveryCodesStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Error getting recovery codes status for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recovery codes status",
        )


@router.post("/regenerate", response_model=GenerateRecoveryCodesResponse)
async def regenerate_recovery_codes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate recovery codes (alias for generate).
    
    This revokes all existing codes and creates new ones.
    """
    # Just call the generate endpoint
    return await generate_recovery_codes(request, current_user, db)
