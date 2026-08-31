"""MFA Recovery Routes - Sprint 8.3.1 Phase 4

API endpoints for MFA recovery code management.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user
from api.models.user import User
from api.models.security import MFARecoveryCode
from api.services.mfa_recovery_service import MFARecoveryService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/mfa/recovery", tags=["mfa-recovery"])


# Request/Response Models

class VerifyRecoveryCodeRequest(BaseModel):
    """Request to verify a recovery code."""
    code: str = Field(..., description="Recovery code in format XXXX-XXXX-XXXX-XXXX")


def _generate_codes(db: Session, user_id, count: int = 10) -> List[str]:
    """Sync helper: delete old codes and create a fresh set."""
    db.query(MFARecoveryCode).filter(MFARecoveryCode.user_id == user_id).delete()

    codes = []
    for _ in range(count):
        code = MFARecoveryService._generate_recovery_code()
        db.add(MFARecoveryCode(
            user_id=user_id,
            code_hash=MFARecoveryService._hash_recovery_code(code),
            is_used=False,
        ))
        codes.append(code)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.mfa_recovery_codes_generated_at = datetime.now(timezone.utc)

    db.commit()
    return codes


# Endpoints

@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_recovery_codes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new set of MFA recovery codes."""
    codes = _generate_codes(db, current_user.id, count=10)

    logger.info(f"Generated {len(codes)} recovery codes for user {current_user.id}")
    return {"codes": codes}


@router.post("/regenerate", status_code=status.HTTP_200_OK)
async def regenerate_recovery_codes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate recovery codes (revokes old set and creates new ones)."""
    codes = _generate_codes(db, current_user.id, count=10)

    logger.info(f"Regenerated {len(codes)} recovery codes for user {current_user.id}")
    return {"codes": codes}


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_recovery_code(
    request: Request,
    body: VerifyRecoveryCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify a recovery code. Marks the code as used (single-use)."""
    code_hash = MFARecoveryService._hash_recovery_code(body.code)

    recovery_code = (
        db.query(MFARecoveryCode)
        .filter(
            MFARecoveryCode.user_id == current_user.id,
            MFARecoveryCode.code_hash == code_hash,
            MFARecoveryCode.is_used == False,
        )
        .first()
    )

    if not recovery_code:
        logger.warning(f"Invalid or already used recovery code for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used recovery code",
        )

    # Mark as used
    recovery_code.is_used = True
    recovery_code.used_at = datetime.now(timezone.utc)
    recovery_code.used_from_ip = request.client.host if request.client else None
    db.commit()

    logger.info(f"Recovery code used for user {current_user.id}")
    return {"valid": True}

