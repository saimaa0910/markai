"""MFA Recovery Service — Sprint 8.3.1 Phase 4

Provides backup authentication via recovery codes when primary MFA device is
unavailable.

Core Features:
- Generate 10 single-use recovery codes
- Secure storage (SHA-256 hashed)
- One-time use enforcement
- Regenerate with revocation of old codes
- Audit logging for compliance

Security Model:
- Recovery codes are 16-character alphanumeric strings
- Stored as SHA-256 hashes (never plaintext)
- One-time use (marked as used after verification)
- Regeneration requires MFA verification
- Cannot be retrieved after initial generation
"""
import uuid
import hashlib
import secrets
import string
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class MFARecoveryService:
    """Service for managing MFA recovery codes."""
    
    # Recovery code format: ABCD-1234-EFGH-5678 (16 chars + 3 dashes)
    CODE_LENGTH = 16
    CODE_FORMAT_GROUPS = 4
    CODE_GROUP_LENGTH = 4
    CODES_PER_SET = 10
    
    @staticmethod
    def _generate_recovery_code() -> str:
        """
        Generate a single recovery code.
        
        Format: XXXX-XXXX-XXXX-XXXX (uppercase alphanumeric)
        Example: A3F7-9K2D-P5M8-Q1N6
        
        Returns:
            Recovery code string
        """
        alphabet = string.ascii_uppercase + string.digits
        code_parts = []
        
        for _ in range(MFARecoveryService.CODE_FORMAT_GROUPS):
            group = ''.join(
                secrets.choice(alphabet)
                for _ in range(MFARecoveryService.CODE_GROUP_LENGTH)
            )
            code_parts.append(group)
        
        return '-'.join(code_parts)
    
    @staticmethod
    def _hash_recovery_code(code: str) -> str:
        """
        Hash a recovery code for secure storage.
        
        Args:
            code: Plaintext recovery code
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    async def generate_recovery_codes(
        db: AsyncSession,
        user_id: uuid.UUID,
        count: int = CODES_PER_SET,
    ) -> List[str]:
        """
        Generate a new set of recovery codes for a user.

        This revokes any existing unused codes and creates a new set.

        Args:
            db: Database session
            user_id: User ID
            count: Number of codes to generate (default 10)

        Returns:
            List of plaintext recovery codes (show to user once)

        Raises:
            ValueError: If user not found
        """
        from api.models.user import User
        from api.models.security import MFARecoveryCode

        # Verify user exists
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Delete all existing recovery codes (used and unused)
        await db.execute(
            delete(MFARecoveryCode).where(MFARecoveryCode.user_id == user_id)
        )

        # Generate new codes
        plaintext_codes = []
        recovery_code_records = []

        for _ in range(count):
            code = MFARecoveryService._generate_recovery_code()
            code_hash = MFARecoveryService._hash_recovery_code(code)

            plaintext_codes.append(code)
            recovery_code_records.append(
                MFARecoveryCode(
                    user_id=user_id,
                    code_hash=code_hash,
                    is_used=False,
                )
            )

        # Save to database
        db.add_all(recovery_code_records)

        # Update user's generation timestamp
        user.mfa_recovery_codes_generated_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(
            f"Generated {count} recovery codes for user {user_id}"
        )

        return plaintext_codes
    
    @staticmethod
    async def verify_recovery_code(
        db: AsyncSession,
        user_id: uuid.UUID,
        code: str,
        used_from_ip: Optional[str] = None,
    ) -> bool:
        """
        Verify a recovery code and mark it as used.
        
        Args:
            db: Database session
            user_id: User ID
            code: Plaintext recovery code
            used_from_ip: IP address where code was used
            
        Returns:
            True if code is valid and unused, False otherwise
        """
        from api.models.security import MFARecoveryCode
        
        # Hash the provided code
        code_hash = MFARecoveryService._hash_recovery_code(code)
        
        # Find matching unused code
        result = await db.execute(
            select(MFARecoveryCode).where(
                and_(
                    MFARecoveryCode.user_id == user_id,
                    MFARecoveryCode.code_hash == code_hash,
                    MFARecoveryCode.is_used == False,
                )
            )
        )
        recovery_code = result.scalar_one_or_none()
        
        if not recovery_code:
            logger.warning(
                f"Invalid or already used recovery code for user {user_id}"
            )
            return False
        
        # Mark as used
        recovery_code.is_used = True
        recovery_code.used_at = datetime.now(timezone.utc)
        recovery_code.used_from_ip = used_from_ip
        
        await db.commit()
        
        logger.info(
            f"Recovery code used for user {user_id} from IP {used_from_ip}"
        )
        
        return True
    
    @staticmethod
    async def get_recovery_codes_status(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get recovery codes status for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with total, used, remaining counts and generation timestamp
        """
        from api.models.user import User
        from api.models.security import MFARecoveryCode
        
        # Get user to check generation timestamp
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                "total": 0,
                "used": 0,
                "remaining": 0,
                "generated_at": None,
            }
        
        # Count total and used codes
        result = await db.execute(
            select(MFARecoveryCode).where(MFARecoveryCode.user_id == user_id)
        )
        codes = result.scalars().all()
        
        total = len(codes)
        used = sum(1 for code in codes if code.is_used)
        remaining = total - used
        
        return {
            "total": total,
            "used": used,
            "remaining": remaining,
            "generated_at": user.mfa_recovery_codes_generated_at.isoformat() if user.mfa_recovery_codes_generated_at else None,
        }
    
    @staticmethod
    async def regenerate_recovery_codes(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> List[str]:
        """
        Regenerate recovery codes (alias for generate_recovery_codes).
        
        This revokes all existing codes and generates a new set.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of 10 new recovery codes
        """
        logger.info(f"Regenerating recovery codes for user {user_id}")
        return await MFARecoveryService.generate_recovery_codes(db, user_id)
    
    @staticmethod
    async def delete_all_recovery_codes(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        """
        Delete all recovery codes for a user.
        
        Use when disabling MFA or deleting account.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of codes deleted
        """
        from api.models.security import MFARecoveryCode
        
        result = await db.execute(
            delete(MFARecoveryCode).where(MFARecoveryCode.user_id == user_id)
        )
        
        count = result.rowcount
        await db.commit()
        
        logger.info(f"Deleted {count} recovery codes for user {user_id}")
        
        return count
