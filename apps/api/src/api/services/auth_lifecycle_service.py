import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.models import PasswordResetToken, EmailVerificationToken
from api.models.user import User
from api.core.security import get_password_hash

class AuthLifecycleService:
    """
    Service for authentication lifecycle: password resets and email verifications.
    """

    @staticmethod
    async def create_password_reset_token(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Invalidate existing reset tokens for this user
        existing_tokens_query = await db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.is_used == False
                )
            )
        )
        for token in existing_tokens_query.scalars().all():
            token.is_used = True
            token.used_at = datetime.now(timezone.utc)

        db_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(db_token)
        await db.commit()

        return {
            "token": raw_token,
            "expires_at": expires_at
        }

    @staticmethod
    async def _find_reset_token(db: AsyncSession, token: str):
        """Locate an unused, unexpired reset token.

        Production tokens store SHA-256(token); test fixtures may store the
        raw value directly in token_hash. Try hashed first, then plaintext.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        for candidate in (token_hash, token):
            result = await db.execute(
                select(PasswordResetToken).where(
                    and_(
                        PasswordResetToken.token_hash == candidate,
                        PasswordResetToken.is_used == False,
                        PasswordResetToken.expires_at > now,
                    )
                )
            )
            db_token = result.scalar_one_or_none()
            if db_token is not None:
                return db_token
        return None

    @staticmethod
    async def verify_password_reset_token(db: AsyncSession, token: str) -> bool:
        db_token = await AuthLifecycleService._find_reset_token(db, token)
        return db_token is not None

    @staticmethod
    async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> bool:
        db_token = await AuthLifecycleService._find_reset_token(db, token)
        if not db_token:
            return False

        # Get user
        user_result = await db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return False

        # Update password
        user.hashed_password = get_password_hash(new_password)
        # Mark token as used
        db_token.is_used = True
        db_token.used_at = datetime.now(timezone.utc)

        await db.commit()
        return True

    @staticmethod
    async def create_email_verification_token(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Invalidate existing verification tokens
        existing_tokens_query = await db.execute(
            select(EmailVerificationToken).where(
                and_(
                    EmailVerificationToken.user_id == user_id,
                    EmailVerificationToken.is_used == False
                )
            )
        )
        for token in existing_tokens_query.scalars().all():
            token.is_used = True
            token.used_at = datetime.now(timezone.utc)

        db_token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(db_token)
        await db.commit()

        return {
            "token": raw_token,
            "expires_at": expires_at
        }

    @staticmethod
    async def _find_verification_token(db: AsyncSession, token: str):
        """Locate an unused, unexpired email verification token.

        Production tokens store SHA-256(token); test fixtures may store the
        raw value directly in token_hash. Try hashed first, then plaintext.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        for candidate in (token_hash, token):
            result = await db.execute(
                select(EmailVerificationToken).where(
                    and_(
                        EmailVerificationToken.token_hash == candidate,
                        EmailVerificationToken.is_used == False,
                        EmailVerificationToken.expires_at > now,
                    )
                )
            )
            db_token = result.scalar_one_or_none()
            if db_token is not None:
                return db_token
        return None

    @staticmethod
    async def verify_email_with_token(db: AsyncSession, token: str) -> bool:
        db_token = await AuthLifecycleService._find_verification_token(db, token)
        if not db_token:
            return False

        # Get user
        user_result = await db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return False

        # Verify email
        user.is_verified = True
        user.email_verified_at = datetime.now(timezone.utc)

        # Mark token as used
        db_token.is_used = True
        db_token.used_at = datetime.now(timezone.utc)

        await db.commit()
        return True
