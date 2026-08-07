"""
Email Verification Token Model
================================
Single-use, time-limited tokens for email address verification.

Security Properties:
- 128-bit entropy (secrets.token_urlsafe(32))
- SHA-256 hash stored (plaintext never persisted)
- Single-use: is_used=TRUE after consumption
- Expires 24h after creation
- Only one active token per user at a time (old tokens invalidated on resend)
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database.base import Base


class EmailVerificationToken(Base):
    """
    Single-use email verification token.

    Flow:
    1. User registers → token created, email sent
    2. User clicks link → token validated (hash, expiry, is_used)
    3. Token consumed → is_used=True, user.is_verified=True
    4. Resend → old pending tokens marked is_used=True, new token created
    """
    __tablename__ = "email_verification_tokens"

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_email_verification_token_hash"),
        Index("idx_email_verification_user_id", "user_id"),
        Index("idx_email_verification_expires_at", "expires_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        comment="SHA-256 of the raw token — plaintext NEVER stored",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="24 hours from creation",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE after successful verification",
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP of the verification request"
    )
