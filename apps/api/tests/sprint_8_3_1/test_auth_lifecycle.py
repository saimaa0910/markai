"""Sprint 8.3.1 Phase 2: Auth Lifecycle Tests

Comprehensive test suite for authentication lifecycle features.
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.models.user import User
from api.models.auth import PasswordResetToken, EmailVerificationToken
from api.services.auth_lifecycle_service import AuthLifecycleService
from api.core.security import get_password_hash, verify_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create test user."""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("oldpassword"),
        full_name="Test User",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


class TestPasswordReset:
    """Test password reset flow."""
    
    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, client, test_user, db):
        """Test requesting password reset successfully."""
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify token created
        from sqlalchemy import select
        result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == test_user.id
            )
        )
        token = result.scalar_one_or_none()
        assert token is not None
        assert not token.is_used
    
    @pytest.mark.asyncio
    async def test_request_password_reset_invalid_email(self, client):
        """Test requesting reset with invalid email."""
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_verify_reset_token_success(self, client, test_user, db):
        """Test verifying password reset token."""
        # Create reset token
        token = PasswordResetToken(
            user_id=test_user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False,
        )
        db.add(token)
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/password-reset/verify",
            json={"token": token.token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    @pytest.mark.asyncio
    async def test_verify_reset_token_expired(self, client, test_user, db):
        """Test verifying expired reset token."""
        # Create expired token
        token = PasswordResetToken(
            user_id=test_user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_used=False,
        )
        db.add(token)
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/password-reset/verify",
            json={"token": token.token},
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, client, test_user, db):
        """Test resetting password successfully."""
        # Create reset token
        token = PasswordResetToken(
            user_id=test_user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False,
        )
        db.add(token)
        await db.commit()
        
        new_password = "NewPassword123!"
        response = client.post(
            "/api/v1/auth/password-reset/reset",
            json={
                "token": token.token,
                "new_password": new_password,
            },
        )
        
        assert response.status_code == 200
        
        # Verify password changed
        await db.refresh(test_user)
        assert verify_password(new_password, test_user.hashed_password)
        
        # Verify token marked as used
        await db.refresh(token)
        assert token.is_used
    
    @pytest.mark.asyncio
    async def test_reset_password_already_used_token(self, client, test_user, db):
        """Test resetting password with already used token."""
        # Create used token
        token = PasswordResetToken(
            user_id=test_user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=True,
        )
        db.add(token)
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/password-reset/reset",
            json={
                "token": token.token,
                "new_password": "NewPassword123!",
            },
        )
        
        assert response.status_code == 400


class TestEmailVerification:
    """Test email verification flow."""
    
    @pytest.mark.asyncio
    async def test_request_email_verification_success(self, client, test_user, db):
        """Test requesting email verification successfully."""
        from api.core.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/auth/email-verification/request",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        
        # Verify token created
        from sqlalchemy import select
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == test_user.id
            )
        )
        ver_token = result.scalar_one_or_none()
        assert ver_token is not None
    
    @pytest.mark.asyncio
    async def test_request_verification_already_verified(self, client, test_user, db):
        """Test requesting verification when already verified."""
        # Mark user as verified
        test_user.is_verified = True
        test_user.email_verified_at = datetime.now(timezone.utc)
        await db.commit()
        
        from api.core.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/auth/email-verification/request",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, client, test_user, db):
        """Test verifying email successfully."""
        # Create verification token
        ver_token = EmailVerificationToken(
            user_id=test_user.id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_used=False,
        )
        db.add(ver_token)
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": ver_token.token},
        )
        
        assert response.status_code == 200
        
        # Verify user marked as verified
        await db.refresh(test_user)
        assert test_user.is_verified
        assert test_user.email_verified_at is not None
        
        # Verify token marked as used
        await db.refresh(ver_token)
        assert ver_token.is_used


class TestAccountLockout:
    """Test account lockout features."""
    
    @pytest.mark.asyncio
    async def test_failed_login_increments_count(self, client, test_user, db):
        """Test failed login increments failed login count."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        
        # Verify failed count incremented
        await db.refresh(test_user)
        assert test_user.failed_login_count > 0
    
    @pytest.mark.asyncio
    async def test_account_locked_after_max_attempts(self, client, test_user, db):
        """Test account locked after max failed attempts."""
        # Make multiple failed login attempts
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "wrongpassword",
                },
            )
        
        # Verify account locked
        await db.refresh(test_user)
        assert test_user.locked_until is not None
        assert test_user.locked_until > datetime.now(timezone.utc)
    
    @pytest.mark.asyncio
    async def test_locked_account_cannot_login(self, client, test_user, db):
        """Test locked account cannot login even with correct password."""
        # Lock account
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        test_user.failed_login_count = 5
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "oldpassword",
            },
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "locked" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_successful_login_resets_failed_count(self, client, test_user, db):
        """Test successful login resets failed login count."""
        # Set failed count
        test_user.failed_login_count = 2
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "oldpassword",
            },
        )
        
        assert response.status_code == 200
        
        # Verify failed count reset
        await db.refresh(test_user)
        assert test_user.failed_login_count == 0


class TestAuthLifecycleService:
    """Test AuthLifecycleService methods."""
    
    @pytest.mark.asyncio
    async def test_create_password_reset_token(self, db, test_user):
        """Test creating password reset token."""
        token_data = await AuthLifecycleService.create_password_reset_token(
            db=db,
            user_id=test_user.id,
        )
        
        assert "token" in token_data
        assert "expires_at" in token_data
    
    @pytest.mark.asyncio
    async def test_verify_password_reset_token(self, db, test_user):
        """Test verifying password reset token."""
        # Create token
        token_data = await AuthLifecycleService.create_password_reset_token(
            db=db,
            user_id=test_user.id,
        )
        
        # Verify token
        is_valid = await AuthLifecycleService.verify_password_reset_token(
            db=db,
            token=token_data["token"],
        )
        
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_reset_password_with_token(self, db, test_user):
        """Test resetting password with valid token."""
        # Create token
        token_data = await AuthLifecycleService.create_password_reset_token(
            db=db,
            user_id=test_user.id,
        )
        
        # Reset password
        new_password = "NewSecurePassword123!"
        success = await AuthLifecycleService.reset_password_with_token(
            db=db,
            token=token_data["token"],
            new_password=new_password,
        )
        
        assert success
        
        # Verify password changed
        await db.refresh(test_user)
        assert verify_password(new_password, test_user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_create_email_verification_token(self, db, test_user):
        """Test creating email verification token."""
        token_data = await AuthLifecycleService.create_email_verification_token(
            db=db,
            user_id=test_user.id,
        )
        
        assert "token" in token_data
        assert "expires_at" in token_data
    
    @pytest.mark.asyncio
    async def test_verify_email_with_token(self, db, test_user):
        """Test verifying email with valid token."""
        # Create token
        token_data = await AuthLifecycleService.create_email_verification_token(
            db=db,
            user_id=test_user.id,
        )
        
        # Verify email
        success = await AuthLifecycleService.verify_email_with_token(
            db=db,
            token=token_data["token"],
        )
        
        assert success
        
        # Verify user marked as verified
        await db.refresh(test_user)
        assert test_user.is_verified
        assert test_user.email_verified_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
