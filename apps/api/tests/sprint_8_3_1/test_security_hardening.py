"""Sprint 8.3.1 Phase 4: Security Hardening Tests

Comprehensive test suite for advanced security features.
"""
import pytest
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.models.user import User
from api.models.security import TrustedDevice, MFARecoveryCode, RateLimitLog
from api.models.auth import AuditLog
from api.services.device_trust_service import DeviceTrustService
from api.services.mfa_recovery_service import MFARecoveryService
from api.services.rate_limit_service import RateLimitService
from api.services.audit_log_service import AuditLogService
from api.core.security import create_access_token, get_password_hash


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        trusted_devices_enabled=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


class TestDeviceTrust:
    """Test trusted device management."""
    
    @pytest.mark.asyncio
    async def test_trust_device_success(self, client, test_user, db):
        """Test trusting a device successfully."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/security/devices/trust",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "device_name": "My Laptop",
                "device_fingerprint": hashlib.sha256(b"unique_device_id").hexdigest(),
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
        assert data["trusted"] is True
    
    @pytest.mark.asyncio
    async def test_list_trusted_devices(self, client, test_user, db):
        """Test listing trusted devices."""
        # Create trusted device
        device = TrustedDevice(
            user_id=test_user.id,
            device_name="Test Device",
            device_fingerprint=hashlib.sha256(b"test").hexdigest(),
            trusted_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add(device)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/security/devices/trusted",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["devices"]) >= 1
    
    @pytest.mark.asyncio
    async def test_revoke_device_success(self, client, test_user, db):
        """Test revoking a trusted device."""
        # Create trusted device
        device = TrustedDevice(
            user_id=test_user.id,
            device_name="Test Device",
            device_fingerprint=hashlib.sha256(b"test").hexdigest(),
            trusted_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add(device)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.delete(
            f"/api/v1/security/devices/trusted/{device.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 204
        
        # Verify device revoked
        await db.refresh(device)
        assert not device.is_active
    
    @pytest.mark.asyncio
    async def test_revoke_all_devices(self, client, test_user, db):
        """Test revoking all trusted devices."""
        # Create multiple devices
        for i in range(3):
            device = TrustedDevice(
                user_id=test_user.id,
                device_name=f"Device {i}",
                device_fingerprint=hashlib.sha256(f"device_{i}".encode()).hexdigest(),
                trusted_at=datetime.now(timezone.utc),
                is_active=True,
            )
            db.add(device)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.delete(
            "/api/v1/security/devices/trusted/all",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["revoked_count"] >= 3


class TestMFARecovery:
    """Test MFA recovery code features."""
    
    @pytest.mark.asyncio
    async def test_generate_recovery_codes(self, client, test_user, db):
        """Test generating MFA recovery codes."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/security/mfa/recovery/generate",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        assert len(data["codes"]) == 10  # Default count
        
        # Verify codes created in database
        await db.refresh(test_user)
        assert test_user.mfa_recovery_codes_generated_at is not None
    
    @pytest.mark.asyncio
    async def test_verify_recovery_code_success(self, client, test_user, db):
        """Test verifying valid recovery code."""
        # Generate recovery codes
        codes = await MFARecoveryService.generate_recovery_codes(
            db=db,
            user_id=test_user.id,
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.post(
            "/api/v1/security/mfa/recovery/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": codes[0]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    @pytest.mark.asyncio
    async def test_recovery_code_single_use(self, client, test_user, db):
        """Test recovery codes are single-use."""
        # Generate recovery codes
        codes = await MFARecoveryService.generate_recovery_codes(
            db=db,
            user_id=test_user.id,
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        # Use code once
        response1 = client.post(
            "/api/v1/security/mfa/recovery/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": codes[0]},
        )
        assert response1.status_code == 200
        
        # Try to use same code again
        response2 = client.post(
            "/api/v1/security/mfa/recovery/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": codes[0]},
        )
        assert response2.status_code == 400
    
    @pytest.mark.asyncio
    async def test_regenerate_recovery_codes(self, client, test_user, db):
        """Test regenerating recovery codes invalidates old ones."""
        # Generate first set
        codes1 = await MFARecoveryService.generate_recovery_codes(
            db=db,
            user_id=test_user.id,
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        # Regenerate
        response = client.post(
            "/api/v1/security/mfa/recovery/regenerate",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["codes"]) == 10
        
        # Old codes should not work
        verify_response = client.post(
            "/api/v1/security/mfa/recovery/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": codes1[0]},
        )
        assert verify_response.status_code == 400


class TestRateLimiting:
    """Test rate limiting features."""
    
    @pytest.mark.asyncio
    async def test_login_rate_limit_enforced(self, client, test_user, db):
        """Test rate limiting on login endpoint."""
        # Make multiple rapid login attempts
        for i in range(6):  # Exceed limit
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "wrongpassword",
                },
            )
            
            if i < 5:
                assert response.status_code in [200, 401]  # Normal or auth failure
            else:
                assert response.status_code == 429  # Rate limited
    
    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self, client, test_user, db):
        """Test rate limit resets after time window."""
        # This test would need to wait or mock time
        pass  # Implementation depends on time mocking strategy
    
    @pytest.mark.asyncio
    async def test_rate_limit_per_endpoint(self, client, test_user, db):
        """Test rate limits are per-endpoint."""
        # Rate limits on login shouldn't affect other endpoints
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": "wrong"},
            )
        
        # Other endpoints should still work
        token = create_access_token(data={"sub": str(test_user.id)})
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestAuditLogging:
    """Test audit logging features."""
    
    @pytest.mark.asyncio
    async def test_audit_log_created_on_login(self, client, test_user, db):
        """Test audit log created on login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password",
            },
        )
        
        assert response.status_code == 200
        
        # Verify audit log created
        from sqlalchemy import select
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.user_id == test_user.id,
                AuditLog.event_type == "login",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
    
    @pytest.mark.asyncio
    async def test_get_audit_logs(self, client, test_user, db):
        """Test retrieving audit logs."""
        # Create audit log
        await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="test_event",
            ip_address="127.0.0.1",
            user_agent="Test",
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/security/audit/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert len(data["logs"]) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_event_type(self, client, test_user, db):
        """Test filtering audit logs by event type."""
        # Create multiple log types
        await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="login",
            ip_address="127.0.0.1",
        )
        await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="password_change",
            ip_address="127.0.0.1",
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/security/audit/logs",
            headers={"Authorization": f"Bearer {token}"},
            params={"event_type": "login"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(log["event_type"] == "login" for log in data["logs"])
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_json(self, client, test_user, db):
        """Test exporting audit logs in JSON format."""
        await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="test",
            ip_address="127.0.0.1",
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/security/audit/logs/export",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "json"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_csv(self, client, test_user, db):
        """Test exporting audit logs in CSV format."""
        await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="test",
            ip_address="127.0.0.1",
        )
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/security/audit/logs/export",
            headers={"Authorization": f"Bearer {token}"},
            params={"format": "csv"},
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]


class TestSecurityServices:
    """Test security service methods."""
    
    @pytest.mark.asyncio
    async def test_device_trust_service(self, db, test_user):
        """Test DeviceTrustService methods."""
        # Trust device
        device_data = await DeviceTrustService.trust_device(
            db=db,
            user_id=test_user.id,
            device_name="Test Device",
            device_fingerprint=hashlib.sha256(b"test").hexdigest(),
        )
        
        assert "device_id" in device_data
        
        # Verify device
        is_trusted = await DeviceTrustService.verify_device(
            db=db,
            user_id=test_user.id,
            device_fingerprint=device_data["device_fingerprint"],
        )
        
        assert is_trusted
    
    @pytest.mark.asyncio
    async def test_mfa_recovery_service(self, db, test_user):
        """Test MFARecoveryService methods."""
        # Generate codes
        codes = await MFARecoveryService.generate_recovery_codes(
            db=db,
            user_id=test_user.id,
            count=10,
        )
        
        assert len(codes) == 10
        
        # Verify code
        is_valid = await MFARecoveryService.verify_recovery_code(
            db=db,
            user_id=test_user.id,
            code=codes[0],
        )
        
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_rate_limit_service(self, db, test_user):
        """Test RateLimitService methods."""
        identifier = f"test_{test_user.id}"
        
        # Check rate limit (should allow)
        is_allowed = await RateLimitService.check_rate_limit(
            db=db,
            identifier=identifier,
            endpoint="test",
            max_attempts=5,
            window_seconds=60,
        )
        
        assert is_allowed
    
    @pytest.mark.asyncio
    async def test_audit_log_service(self, db, test_user):
        """Test AuditLogService methods."""
        # Log event
        log_id = await AuditLogService.log_event(
            db=db,
            user_id=test_user.id,
            event_type="test_event",
            ip_address="127.0.0.1",
            user_agent="Test",
            metadata={"key": "value"},
        )
        
        assert log_id is not None
        
        # Get logs
        logs = await AuditLogService.get_user_logs(
            db=db,
            user_id=test_user.id,
        )
        
        assert len(logs) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
