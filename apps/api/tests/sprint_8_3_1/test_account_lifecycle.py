"""Sprint 8.3.1 Phase 3: Account Lifecycle Tests

Comprehensive test suite for account lifecycle and data management features.
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.models.user import User
from api.services.account_lifecycle_service import AccountLifecycleService
from api.core.security import create_access_token, get_password_hash


from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    org = Organization(
        id=uuid.uuid4(),
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        plan_tier="enterprise",
    )
    db.add(org)
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.ADMIN,
        is_primary=True,
        status="active",
    )
    db.add(user_org)
    await db.commit()
    await db.refresh(user)
    return user


class TestAccountDeactivation:
    """Test account deactivation features."""
    
    @pytest.mark.asyncio
    async def test_deactivate_account_success(self, client, test_user, db):
        """Test self-deactivating account successfully."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/account/lifecycle/deactivate",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "Taking a break"},
        )
        
        assert response.status_code == 200
        
        # Verify account deactivated
        await db.refresh(test_user)
        assert not test_user.is_active
        assert test_user.deactivated_at is not None
        assert test_user.deactivation_reason == "Taking a break"
    
    @pytest.mark.asyncio
    async def test_reactivate_account_success(self, client, test_user, db):
        """Test reactivating deactivated account."""
        # Deactivate first
        test_user.is_active = False
        test_user.deactivated_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Try to reactivate
        response = client.post(
            "/api/v1/account/lifecycle/reactivate",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
        
        # Verify account reactivated
        await db.refresh(test_user)
        assert test_user.is_active
        assert test_user.deactivated_at is None
    
    @pytest.mark.asyncio
    async def test_cannot_login_when_deactivated(self, client, test_user, db):
        """Test that deactivated users cannot login."""
        # Deactivate account
        test_user.is_active = False
        test_user.deactivated_at = datetime.now(timezone.utc)
        await db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password",
            },
        )
        
        assert response.status_code == 403


class TestAccountDeletion:
    """Test account deletion features."""
    
    @pytest.mark.asyncio
    async def test_request_deletion_success(self, client, test_user, db):
        """Test requesting account deletion."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/account/lifecycle/request-deletion",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "No longer need the service"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scheduled_deletion_at" in data
        
        # Verify deletion scheduled
        await db.refresh(test_user)
        assert test_user.deletion_requested_at is not None
        assert test_user.scheduled_deletion_at is not None
        assert test_user.deletion_reason == "No longer need the service"
    
    @pytest.mark.asyncio
    async def test_cancel_deletion_success(self, client, test_user, db):
        """Test canceling scheduled deletion."""
        # Schedule deletion
        test_user.deletion_requested_at = datetime.now(timezone.utc)
        test_user.scheduled_deletion_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/account/lifecycle/cancel-deletion",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        
        # Verify deletion canceled
        await db.refresh(test_user)
        assert test_user.deletion_requested_at is None
        assert test_user.scheduled_deletion_at is None
    
    @pytest.mark.asyncio
    async def test_confirm_deletion_success(self, client, test_user, db):
        """Test confirming immediate deletion."""
        # Schedule deletion
        test_user.deletion_requested_at = datetime.now(timezone.utc)
        test_user.scheduled_deletion_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/account/lifecycle/confirm-deletion",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        
        # Verify account marked as deleted
        await db.refresh(test_user)
        assert test_user.deleted_at is not None
    
    @pytest.mark.asyncio
    async def test_get_lifecycle_status(self, client, test_user, db):
        """Test getting account lifecycle status."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/account/lifecycle/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_active" in data
        assert "deletion_scheduled" in data


class TestDataExport:
    """Test GDPR data export features."""
    
    @pytest.mark.asyncio
    async def test_export_user_data_json(self, client, test_user, db):
        """Test exporting user data in JSON format."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/account/lifecycle/data-export",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "json"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Verify export tracked
        await db.refresh(test_user)
        assert test_user.last_export_at is not None
        assert test_user.export_count > 0
    
    @pytest.mark.asyncio
    async def test_export_user_data_csv(self, client, test_user, db):
        """Test exporting user data in CSV format."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/account/lifecycle/data-export",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "csv"},
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_export_includes_all_user_data(self, client, test_user, db):
        """Test that export includes all user data."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/account/lifecycle/data-export",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "json"},
        )
        
        data = response.json()
        assert "user" in data
        assert "sessions" in data
        assert "audit_logs" in data


class TestPrivacyDashboard:
    """Test privacy dashboard features."""
    
    @pytest.mark.asyncio
    async def test_get_privacy_dashboard(self, client, test_user, db):
        """Test getting privacy dashboard data."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/account/lifecycle/privacy-dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data_summary" in data
        assert "export_history" in data
        assert "deletion_status" in data


class TestAdminOperations:
    """Test admin account lifecycle operations."""
    
    @pytest.fixture
    async def admin_user(self, db):
        admin = User(
            email=f"admin_{uuid.uuid4()}@example.com",
            hashed_password=get_password_hash("adminpass"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin
    
    @pytest.mark.asyncio
    async def test_admin_deactivate_user(self, client, test_user, admin_user, db):
        """Test admin deactivating user account."""
        token = create_access_token(data={"sub": str(admin_user.id)})
        
        response = client.post(
            f"/api/v1/account/lifecycle/admin/deactivate/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "Policy violation"},
        )
        
        assert response.status_code == 200
        
        # Verify user deactivated
        await db.refresh(test_user)
        assert not test_user.is_active
    
    @pytest.mark.asyncio
    async def test_admin_unlock_account(self, client, test_user, admin_user, db):
        """Test admin unlocking locked account."""
        # Lock account
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        test_user.failed_login_count = 5
        await db.commit()
        
        token = create_access_token(data={"sub": str(admin_user.id)})
        
        response = client.post(
            f"/api/v1/account/lifecycle/admin/unlock/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        
        # Verify account unlocked
        await db.refresh(test_user)
        assert test_user.locked_until is None
        assert test_user.failed_login_count == 0
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_admin_deactivate(self, client, test_user, db):
        """Test non-admin cannot perform admin operations."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            f"/api/v1/account/lifecycle/admin/deactivate/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "Test"},
        )
        
        assert response.status_code == 403


class TestAccountLifecycleService:
    """Test AccountLifecycleService methods."""
    
    @pytest.mark.asyncio
    async def test_deactivate_account(self, db, test_user):
        """Test deactivating account via service."""
        result = await AccountLifecycleService.deactivate_account(
            db=db,
            user_id=test_user.id,
            reason="Test deactivation",
        )
        
        assert result["success"]
        await db.refresh(test_user)
        assert not test_user.is_active
    
    @pytest.mark.asyncio
    async def test_request_deletion(self, db, test_user):
        """Test requesting account deletion via service."""
        result = await AccountLifecycleService.request_deletion(
            db=db,
            user_id=test_user.id,
            reason="No longer needed",
        )
        
        assert "scheduled_deletion_at" in result
        await db.refresh(test_user)
        assert test_user.deletion_requested_at is not None
    
    @pytest.mark.asyncio
    async def test_export_user_data(self, db, test_user):
        """Test exporting user data via service."""
        data = await AccountLifecycleService.export_user_data(
            db=db,
            user_id=test_user.id,
        )
        
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        
        # Verify export tracked
        await db.refresh(test_user)
        assert test_user.export_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
