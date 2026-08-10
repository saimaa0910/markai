# Sprint 8.3.1: Authentication Lifecycle
## Testing Guide

**Version**: 1.0.0  
**Audience**: QA Engineers & Developers  
**Last Updated**: 2026-05-21

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [Security Tests](#security-tests)
6. [Performance Tests](#performance-tests)
7. [Manual Test Cases](#manual-test-cases)
8. [Test Automation](#test-automation)
9. [CI/CD Integration](#cicd-integration)

---

## Testing Overview

### Test Scope

Sprint 8.3.1 introduces **40+ new endpoints** and **15+ new database tables** across four phases:

* **Phase 1**: Session Management (4 endpoints)
* **Phase 2**: Auth Lifecycle (6 endpoints)
* **Phase 3**: Account Lifecycle (8 endpoints)
* **Phase 4**: Security Hardening (11 endpoints)

### Test Coverage Goals

* **Unit Tests**: 90%+ code coverage
* **Integration Tests**: All endpoints tested
* **Security Tests**: OWASP Top 10 coverage
* **Performance Tests**: All endpoints benchmarked

### Test Locations

```
markai/apps/api/
├── tests/
│   ├── sprint_8_3_1/
│   │   ├── test_session_management.py
│   │   ├── test_auth_lifecycle.py
│   │   ├── test_account_lifecycle.py
│   │   └── test_security_hardening.py
│   ├── conftest.py
│   └── fixtures/
```

---

## Test Environment Setup

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx faker

# Install security testing tools
pip install bandit safety

# Install performance testing tools
pip install locust
```

### Test Database

```bash
# Create test database
psql -U postgres -c "CREATE DATABASE eaimos_test;"

# Run migrations
export DATABASE_URL="postgresql://postgres:password@localhost/eaimos_test"
alembic upgrade head
```

### Environment Configuration

```env
# .env.test
ENVIRONMENT=test
DATABASE_URL=postgresql://postgres:password@localhost/eaimos_test
SECRET_KEY=test-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Disable external services in tests
SEND_EMAILS=false
ENABLE_REDIS=false
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/sprint_8_3_1/test_session_management.py

# Run specific test
pytest tests/sprint_8_3_1/test_session_management.py::TestSessionListing::test_list_sessions_success

# Run with verbose output
pytest -v

# Run in parallel (faster)
pytest -n auto
```

---

## Unit Tests

### Test Structure

Each test file follows this structure:

```python
import pytest
import uuid
from datetime import datetime, timedelta

# Fixtures
@pytest.fixture
async def test_user(db):
    """Create test user."""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# Test classes
class TestFeatureName:
    """Test specific feature."""
    
    @pytest.mark.asyncio
    async def test_feature_success(self, db, test_user):
        """Test successful operation."""
        # Arrange
        ...
        
        # Act
        result = await service.method()
        
        # Assert
        assert result is not None
        assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_feature_failure(self, db):
        """Test failure case."""
        with pytest.raises(ValueError):
            await service.method(invalid_data)
```

### Phase 1: Session Management Tests

**Test File**: `test_session_management.py`

**Coverage**:
* ✅ Session creation
* ✅ Session listing
* ✅ Session revocation (single)
* ✅ Session revocation (all)
* ✅ Session expiration
* ✅ Session validation
* ✅ Concurrent session limits

**Run tests**:
```bash
pytest tests/sprint_8_3_1/test_session_management.py -v
```

**Expected Output**:
```
test_session_management.py::TestSessionListing::test_list_sessions_success PASSED
test_session_management.py::TestSessionListing::test_list_sessions_unauthorized PASSED
test_session_management.py::TestSessionRevocation::test_revoke_session_success PASSED
test_session_management.py::TestSessionRevocation::test_revoke_session_not_found PASSED
test_session_management.py::TestRevokeAllSessions::test_revoke_all_sessions_success PASSED
...
========================= 25 passed in 3.45s =========================
```

### Phase 2: Auth Lifecycle Tests

**Test File**: `test_auth_lifecycle.py`

**Coverage**:
* ✅ Password reset request
* ✅ Password reset verification
* ✅ Password reset completion
* ✅ Email verification
* ✅ Account lockout
* ✅ Failed login tracking

**Run tests**:
```bash
pytest tests/sprint_8_3_1/test_auth_lifecycle.py -v
```

### Phase 3: Account Lifecycle Tests

**Test File**: `test_account_lifecycle.py`

**Coverage**:
* ✅ Account deactivation
* ✅ Account reactivation
* ✅ Account deletion request
* ✅ Account deletion cancellation
* ✅ Immediate deletion
* ✅ Data export (JSON/CSV)
* ✅ Privacy dashboard

**Run tests**:
```bash
pytest tests/sprint_8_3_1/test_account_lifecycle.py -v
```

### Phase 4: Security Hardening Tests

**Test File**: `test_security_hardening.py`

**Coverage**:
* ✅ Device trust management
* ✅ MFA recovery codes
* ✅ Rate limiting enforcement
* ✅ Audit logging
* ✅ Security event tracking

**Run tests**:
```bash
pytest tests/sprint_8_3_1/test_security_hardening.py -v
```

---

## Integration Tests

### API Integration Tests

**Purpose**: Test full request-response cycle for all endpoints.

**Example Test**:

```python
import httpx
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

class TestSessionManagementAPI:
    """Integration tests for session management endpoints."""
    
    @pytest.mark.asyncio
    async def test_full_session_flow(self, test_user):
        """Test complete session lifecycle."""
        
        # 1. Login (creates session)
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 2. List sessions
        sessions_response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()["sessions"]
        assert len(sessions) >= 1
        
        # 3. Revoke specific session
        session_id = sessions[0]["id"]
        revoke_response = client.delete(
            f"/api/v1/auth/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert revoke_response.status_code == 204
        
        # 4. Verify session revoked
        # (Token should no longer work)
        verify_response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == 401
```

### Database Integration Tests

**Purpose**: Verify database operations, constraints, and transactions.

```python
class TestDatabaseIntegration:
    """Test database operations."""
    
    @pytest.mark.asyncio
    async def test_cascade_delete_sessions(self, db, test_user):
        """Test that deleting user cascades to sessions."""
        # Create sessions
        for _ in range(3):
            session = Session(
                user_id=test_user.id,
                session_token=str(uuid.uuid4()),
                expires_at=datetime.now() + timedelta(days=7)
            )
            db.add(session)
        await db.commit()
        
        # Delete user
        await db.delete(test_user)
        await db.commit()
        
        # Verify sessions deleted
        from sqlalchemy import select
        result = await db.execute(
            select(Session).where(Session.user_id == test_user.id)
        )
        sessions = result.scalars().all()
        assert len(sessions) == 0
```

### Service Integration Tests

**Purpose**: Test service layer interactions.

```python
class TestServiceIntegration:
    """Test service interactions."""
    
    @pytest.mark.asyncio
    async def test_password_reset_service_flow(self, db, test_user):
        """Test complete password reset service flow."""
        # Request reset
        token = await AuthLifecycleService.create_password_reset_token(
            db=db,
            user_id=test_user.id
        )
        
        # Verify token
        is_valid = await AuthLifecycleService.verify_password_reset_token(
            db=db,
            token=token
        )
        assert is_valid
        
        # Reset password
        success = await AuthLifecycleService.reset_password_with_token(
            db=db,
            token=token,
            new_password="NewPassword123!"
        )
        assert success
        
        # Verify password changed
        await db.refresh(test_user)
        assert verify_password("NewPassword123!", test_user.hashed_password)
```

---

## Security Tests

### OWASP Top 10 Testing

#### 1. Broken Access Control

```python
class TestAccessControl:
    """Test authorization and access control."""
    
    @pytest.mark.asyncio
    async def test_cannot_access_other_user_sessions(self, client):
        """Test users cannot access other users' sessions."""
        user1 = await create_test_user("user1@example.com")
        user2 = await create_test_user("user2@example.com")
        
        # Create session for user1
        session1 = await create_session(user1.id)
        
        # Login as user2
        token2 = await login_user(user2.email, "password")
        
        # Try to revoke user1's session as user2
        response = client.delete(
            f"/api/v1/auth/sessions/{session1.id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
```

#### 2. Cryptographic Failures

```python
class TestCryptography:
    """Test cryptographic implementations."""
    
    def test_passwords_are_hashed(self, test_user):
        """Test passwords are never stored in plaintext."""
        # Password should be hashed
        assert test_user.hashed_password != "password"
        assert len(test_user.hashed_password) > 50  # bcrypt hash length
        assert test_user.hashed_password.startswith("$2b$")  # bcrypt format
    
    def test_tokens_are_cryptographically_secure(self):
        """Test tokens use secure random generation."""
        tokens = [secrets.token_urlsafe(32) for _ in range(1000)]
        
        # No duplicates
        assert len(tokens) == len(set(tokens))
        
        # Sufficient length
        assert all(len(t) >= 32 for t in tokens)
```

#### 3. Injection

```python
class TestSQLInjection:
    """Test SQL injection prevention."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_login(self, client):
        """Test login is protected against SQL injection."""
        # Try SQL injection in email field
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin' OR '1'='1",
                "password": "anything"
            }
        )
        
        # Should fail authentication, not execute SQL
        assert response.status_code == 401
```

#### 4. Security Misconfiguration

```python
class TestSecurityHeaders:
    """Test security headers are set."""
    
    def test_security_headers_present(self, client):
        """Test all security headers are set."""
        response = client.get("/api/v1/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "Strict-Transport-Security" in response.headers
```

#### 5. Vulnerable Components

```bash
# Run security audit
safety check

# Run static analysis
bandit -r api/
```

#### 6. Broken Authentication

```python
class TestAuthentication:
    """Test authentication mechanisms."""
    
    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(self, client, test_user):
        """Test account locks after max failed attempts."""
        # Make 5 failed login attempts
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "wrongpassword"
                }
            )
        
        # 6th attempt should be locked
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password"  # Even correct password
            }
        )
        
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()
```

---

## Performance Tests

### Load Testing with Locust

**File**: `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between
import secrets

class EAIMOSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password"
            }
        )
        self.token = response.json()["access_token"]
    
    @task(3)
    def list_sessions(self):
        """List user sessions (common operation)."""
        self.client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def revoke_session(self):
        """Revoke a session (less common)."""
        # Get sessions
        response = self.client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        sessions = response.json()["sessions"]
        
        if len(sessions) > 1:
            # Revoke first session (not current)
            session_id = sessions[1]["id"]
            self.client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
```

**Run load test**:
```bash
# Start locust
locust -f tests/performance/locustfile.py

# Open http://localhost:8089
# Set: 100 users, 10 spawn rate
```

### Benchmark Tests

```python
import pytest
import time

class TestPerformance:
    """Performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_session_list_performance(self, db, test_user):
        """Test session listing performs well with many sessions."""
        # Create 100 sessions
        for _ in range(100):
            session = Session(
                user_id=test_user.id,
                session_token=str(uuid.uuid4()),
                expires_at=datetime.now() + timedelta(days=7)
            )
            db.add(session)
        await db.commit()
        
        # Benchmark query
        start = time.time()
        sessions = await SessionService.get_user_sessions(db, test_user.id)
        duration = time.time() - start
        
        # Should complete in < 100ms
        assert duration < 0.1
        assert len(sessions) == 100
```

---

## Manual Test Cases

### Test Case Template

**Test Case ID**: TC-831-001  
**Feature**: Session Management  
**Priority**: High  
**Pre-conditions**: User is logged in

**Steps**:
1. Navigate to Security Settings
2. Click "Sessions" tab
3. Verify current session is marked
4. Click "Revoke" on another session
5. Confirm revocation

**Expected Result**:
* Session is removed from list
* User on that device is logged out
* Notification is sent

**Actual Result**: [To be filled by tester]

**Status**: [Pass/Fail/Blocked]

### Critical Test Cases

#### TC-831-001: List Active Sessions
**Priority**: High  
**Preconditions**: User has 3+ active sessions

**Steps**:
1. Login on desktop
2. Login on mobile
3. Login on tablet
4. Go to Settings > Security > Sessions
5. Verify all 3 sessions are listed
6. Verify current session is marked

**Expected**: All sessions shown with device info, IP, last active time

---

#### TC-831-002: Revoke Specific Session
**Priority**: High

**Steps**:
1. Login on 2 devices
2. On device 1, go to Sessions
3. Revoke device 2's session
4. On device 2, try to access protected page

**Expected**: Device 2 is logged out immediately

---

#### TC-831-003: Password Reset Flow
**Priority**: Critical

**Steps**:
1. Go to login page
2. Click "Forgot Password?"
3. Enter email
4. Check email inbox
5. Click reset link
6. Enter new password
7. Submit
8. Login with new password

**Expected**: Reset successful, old password no longer works

---

#### TC-831-004: Account Deletion with Grace Period
**Priority**: High

**Steps**:
1. Go to Settings > Account
2. Click "Delete Account"
3. Read warnings
4. Enter password and confirmation
5. Submit
6. Verify 7-day grace period message
7. Login again
8. See deletion warning banner
9. Click "Cancel Deletion"
10. Verify account restored

**Expected**: Account marked for deletion, cancellation works

---

#### TC-831-005: MFA Recovery Code Usage
**Priority**: High

**Steps**:
1. Setup MFA
2. Generate recovery codes
3. Save codes
4. Logout
5. Login with email/password
6. On MFA screen, click "Use Recovery Code"
7. Enter one code
8. Verify login successful
9. Try to use same code again

**Expected**: Code works once, fails on reuse

---

## Test Automation

### Continuous Testing

**GitHub Actions Workflow**:

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run migrations
      run: alembic upgrade head
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/eaimos_test
    
    - name: Run tests
      run: pytest --cov=api --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/eaimos_test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/sprint_8_3_1/
        language: system
        pass_filenames: false
        always_run: true
```

---

## CI/CD Integration

### Test Pipeline Stages

1. **Lint & Format** (1 min)
   * Run black, flake8, mypy
   * Check code formatting

2. **Unit Tests** (3-5 min)
   * Run all unit tests
   * Generate coverage report
   * Fail if coverage < 90%

3. **Integration Tests** (5-8 min)
   * Run API integration tests
   * Test database operations

4. **Security Tests** (2-3 min)
   * Run bandit, safety
   * Check for vulnerabilities

5. **Performance Tests** (5-10 min)
   * Run benchmark tests
   * Check for regressions

### Deployment Gates

**Requirements before production deployment**:
* ✅ All tests passing
* ✅ Code coverage ≥ 90%
* ✅ No security vulnerabilities
* ✅ Performance benchmarks met
* ✅ Manual smoke tests passed
* ✅ Staging environment tested

---

## Test Results

### Expected Coverage

```
============================== test session starts ===============================
platform linux -- Python 3.10.0
plugins: asyncio-0.18.0, cov-3.0.0
collected 156 items

tests/sprint_8_3_1/test_session_management.py ............ [ 25%]
tests/sprint_8_3_1/test_auth_lifecycle.py ............... [ 50%]
tests/sprint_8_3_1/test_account_lifecycle.py ............ [ 75%]
tests/sprint_8_3_1/test_security_hardening.py ........... [100%]

---------- coverage: platform linux, python 3.10.0 -----------
Name                                        Stmts   Miss  Cover
---------------------------------------------------------------
api/routes/auth_session.py                    156      8    95%
api/routes/auth_lifecycle.py                  178     10    94%
api/routes/account_lifecycle.py               203     15    93%
api/routes/device_trust.py                    134      7    95%
api/routes/mfa_recovery.py                    145      9    94%
api/routes/audit_logs.py                       89      5    94%
api/services/session_service.py               167      9    95%
api/services/auth_lifecycle_service.py        189     12    94%
api/services/account_lifecycle_service.py     234     18    92%
api/services/device_trust_service.py          123      7    94%
api/services/mfa_recovery_service.py          156     10    94%
api/services/rate_limit_service.py             98      6    94%
api/services/audit_log_service.py             112      8    93%
---------------------------------------------------------------
TOTAL                                        1984    124    94%

========================= 156 passed in 45.23s =========================
```

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Contact**: qa@markai.com
