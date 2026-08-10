# Sprint 8.3.1: Authentication Lifecycle
## Security Best Practices Guide

**Version**: 1.0.0  
**Audience**: Developers & Security Teams  
**Last Updated**: 2026-05-21

---

## Table of Contents

1. [Authentication Security](#authentication-security)
2. [Session Management](#session-management)
3. [Password Security](#password-security)
4. [Multi-Factor Authentication](#multi-factor-authentication)
5. [Device Trust](#device-trust)
6. [Rate Limiting & Brute Force Protection](#rate-limiting--brute-force-protection)
7. [Audit Logging](#audit-logging)
8. [Data Privacy](#data-privacy)
9. [API Security](#api-security)
10. [Incident Response](#incident-response)

---

## Authentication Security

### Token Management

**✅ Do:**
* Use short-lived access tokens (15-60 minutes)
* Use longer-lived refresh tokens (7-30 days)
* Store tokens securely (httpOnly cookies or secure storage)
* Rotate refresh tokens on use
* Invalidate all tokens on password change

**❌ Don't:**
* Store tokens in localStorage (XSS vulnerable)
* Send tokens in URL parameters
* Use predictable token values
* Reuse tokens across different sessions

**Implementation:**

```python
# Good: Short-lived access token
access_token = create_access_token(
    data={"sub": user.id},
    expires_delta=timedelta(minutes=30)
)

# Good: Secure cookie
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=1800
)
```

### Login Security

**✅ Do:**
* Implement progressive delays on failed attempts
* Log all authentication attempts
* Use CAPTCHA after N failed attempts
* Monitor for credential stuffing patterns
* Enforce account lockout policies

**❌ Don't:**
* Return different errors for invalid email vs. password (user enumeration)
* Allow unlimited login attempts
* Log passwords (even encrypted)
* Skip MFA for "trusted" roles

**Example: Secure Login Response**

```python
# Bad - reveals if email exists
if not user:
    return {"error": "Email not found"}
if not verify_password(password, user.password):
    return {"error": "Incorrect password"}

# Good - generic error message
if not user or not verify_password(password, user.password):
    await log_failed_login(email, ip_address)
    return {"error": "Invalid email or password"}
```

---

## Session Management

### Session Lifecycle

**✅ Do:**
* Set reasonable session expiration (7-30 days max)
* Implement idle timeout (15-60 minutes)
* Revoke sessions on password change
* Allow users to view and revoke sessions
* Track session metadata (IP, device, location)

**❌ Don't:**
* Create sessions without expiration
* Allow unlimited concurrent sessions
* Share sessions across devices
* Trust session data without validation

**Implementation:**

```python
# Session creation with full metadata
async def create_session(
    user_id: UUID,
    ip_address: str,
    user_agent: str,
    device_fingerprint: Optional[str] = None
) -> Session:
    session = Session(
        user_id=user_id,
        session_token=secrets.token_urlsafe(32),
        ip_address=ip_address,
        user_agent=user_agent,
        device_fingerprint=device_fingerprint,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        last_active_at=datetime.now(timezone.utc),
        is_active=True
    )
    await db.add(session)
    await db.commit()
    return session
```

### Session Validation

**✅ Do:**
* Validate session on every request
* Check expiration timestamp
* Verify session is not revoked
* Update last_active_at regularly
* Implement sliding session expiration

**❌ Don't:**
* Trust client-provided session data
* Skip expiration checks
* Forget to clean up expired sessions

---

## Password Security

### Password Requirements

**Minimum Requirements:**
* Length: 12+ characters (16+ recommended)
* Complexity: Mixed case + numbers + special characters
* No common passwords (check against breach databases)
* No personal information (name, email, birthday)
* No sequential or repeated characters

**Implementation:**

```python
import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_password(password: str, user_email: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    
    # Length check
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    # Complexity checks
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letters"
    if not re.search(r"\d", password):
        return False, "Password must contain numbers"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain special characters"
    
    # Check against user email
    email_local = user_email.split("@")[0].lower()
    if email_local in password.lower():
        return False, "Password cannot contain your email address"
    
    # Check common passwords (implement breach database check)
    if is_common_password(password):
        return False, "Password is too common"
    
    return True, "Password is valid"

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Password Reset Security

**✅ Do:**
* Generate cryptographically secure reset tokens
* Set short expiration (1 hour)
* Mark tokens as single-use
* Log all reset attempts
* Invalidate all sessions after reset
* Send confirmation email after reset

**❌ Don't:**
* Use predictable tokens
* Allow token reuse
* Skip email verification
* Allow password reset without rate limiting

```python
import secrets

async def create_password_reset_token(user_id: UUID) -> str:
    """Create secure password reset token."""
    token = secrets.token_urlsafe(32)
    
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_used=False,
        created_at=datetime.now(timezone.utc)
    )
    
    await db.add(reset_token)
    await db.commit()
    
    # Log event
    await AuditLogService.log_event(
        user_id=user_id,
        event_type="password_reset_requested",
        ip_address=request.client.host
    )
    
    return token
```

---

## Multi-Factor Authentication

### MFA Implementation

**✅ Do:**
* Require MFA for all privileged accounts
* Support multiple MFA methods (TOTP, SMS backup)
* Provide recovery codes
* Log all MFA events
* Allow MFA bypass only with recovery codes
* Force MFA setup for new users

**❌ Don't:**
* Store TOTP secrets in plaintext
* Allow MFA disable without re-authentication
* Skip MFA for "trusted" IPs
* Implement SMS as primary MFA (vulnerable to SIM swapping)

**Implementation:**

```python
import pyotp

class MFAService:
    @staticmethod
    async def setup_totp(user_id: UUID) -> dict:
        """Setup TOTP for user."""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="EAIMOS"
        )
        
        # Store encrypted secret
        mfa_method = MFAMethod(
            user_id=user_id,
            method_type="totp",
            secret=encrypt(secret),  # Encrypt!
            is_verified=False,
            created_at=datetime.now(timezone.utc)
        )
        await db.add(mfa_method)
        await db.commit()
        
        return {
            "secret": secret,  # Show once
            "qr_uri": uri,
            "backup_codes": await generate_recovery_codes(user_id)
        }
    
    @staticmethod
    async def verify_totp(user_id: UUID, code: str) -> bool:
        """Verify TOTP code."""
        mfa_method = await get_user_mfa_method(user_id, "totp")
        
        if not mfa_method:
            return False
        
        secret = decrypt(mfa_method.secret)
        totp = pyotp.TOTP(secret)
        
        # Verify with 30-second window
        is_valid = totp.verify(code, valid_window=1)
        
        # Log attempt
        await AuditLogService.log_event(
            user_id=user_id,
            event_type="mfa_verify_attempt",
            metadata={"success": is_valid}
        )
        
        return is_valid
```

### Recovery Codes

**✅ Do:**
* Generate 10-20 recovery codes
* Hash codes before storage (SHA-256)
* Mark codes as single-use
* Force regeneration when count is low
* Log all recovery code usage

**❌ Don't:**
* Store recovery codes in plaintext
* Allow recovery code reuse
* Generate predictable codes

```python
import hashlib

async def generate_recovery_codes(user_id: UUID, count: int = 10) -> list[str]:
    """Generate MFA recovery codes."""
    codes = []
    
    for _ in range(count):
        # Generate code
        code = "-".join([
            secrets.token_hex(2).upper() 
            for _ in range(3)
        ])  # Format: XXXX-XXXX-XXXX
        
        # Hash and store
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        recovery_code = MFARecoveryCode(
            user_id=user_id,
            code_hash=code_hash,
            is_used=False,
            created_at=datetime.now(timezone.utc)
        )
        await db.add(recovery_code)
        
        codes.append(code)
    
    await db.commit()
    
    # Update user
    user.mfa_recovery_codes_generated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return codes
```

---

## Device Trust

### Device Fingerprinting

**✅ Do:**
* Combine multiple device attributes
* Hash fingerprints before storage
* Set reasonable trust duration (30-90 days)
* Allow users to manage trusted devices
* Log all device trust events

**❌ Don't:**
* Trust client-provided fingerprints without validation
* Use single attribute as fingerprint
* Trust devices indefinitely
* Disable MFA completely for trusted devices

**Implementation:**

```python
import hashlib
import json

def generate_device_fingerprint(
    user_agent: str,
    ip_address: str,
    headers: dict
) -> str:
    """Generate device fingerprint."""
    # Combine multiple attributes
    fingerprint_data = {
        "user_agent": user_agent,
        "ip_subnet": ".".join(ip_address.split(".")[:3]),  # /24 subnet
        "accept_language": headers.get("Accept-Language", ""),
        "accept_encoding": headers.get("Accept-Encoding", ""),
        "platform": extract_platform(user_agent),
    }
    
    # Create hash
    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()

async def trust_device(
    user_id: UUID,
    device_name: str,
    device_fingerprint: str,
    trust_duration_days: int = 30
) -> TrustedDevice:
    """Trust a device."""
    trusted_device = TrustedDevice(
        user_id=user_id,
        device_name=device_name,
        device_fingerprint=device_fingerprint,
        trusted_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=trust_duration_days),
        is_active=True
    )
    
    await db.add(trusted_device)
    await db.commit()
    
    # Log event
    await AuditLogService.log_event(
        user_id=user_id,
        event_type="device_trusted",
        metadata={"device_name": device_name}
    )
    
    return trusted_device
```

---

## Rate Limiting & Brute Force Protection

### Rate Limiting Strategy

**Tiered Approach:**

1. **Per-IP limits** - Prevent distributed attacks
2. **Per-account limits** - Prevent targeted attacks
3. **Global limits** - Prevent service abuse

**Implementation:**

```python
class RateLimitService:
    @staticmethod
    async def check_rate_limit(
        identifier: str,
        endpoint: str,
        max_attempts: int,
        window_seconds: int
    ) -> bool:
        """Check if request is within rate limit."""
        
        # Count attempts in window
        window_start = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        
        query = select(func.count(RateLimitLog.id)).where(
            RateLimitLog.identifier == identifier,
            RateLimitLog.endpoint == endpoint,
            RateLimitLog.timestamp >= window_start
        )
        
        result = await db.execute(query)
        attempt_count = result.scalar()
        
        # Check limit
        if attempt_count >= max_attempts:
            # Log rate limit hit
            await AuditLogService.log_event(
                user_id=None,
                event_type="rate_limit_exceeded",
                ip_address=identifier,
                metadata={
                    "endpoint": endpoint,
                    "attempts": attempt_count
                }
            )
            return False
        
        # Log attempt
        rate_log = RateLimitLog(
            identifier=identifier,
            endpoint=endpoint,
            timestamp=datetime.now(timezone.utc)
        )
        await db.add(rate_log)
        await db.commit()
        
        return True
```

### Endpoint-Specific Limits

```python
RATE_LIMITS = {
    "/auth/login": {
        "max_attempts": 5,
        "window_seconds": 900,  # 15 minutes
        "block_duration_seconds": 900
    },
    "/auth/register": {
        "max_attempts": 3,
        "window_seconds": 3600,  # 1 hour
        "block_duration_seconds": 3600
    },
    "/auth/password-reset/request": {
        "max_attempts": 3,
        "window_seconds": 3600,
        "block_duration_seconds": 3600
    },
    "/auth/mfa/verify": {
        "max_attempts": 5,
        "window_seconds": 900,
        "block_duration_seconds": 1800
    }
}
```

---

## Audit Logging

### Events to Log

**Authentication Events:**
* Login attempts (success and failure)
* Logout
* MFA events (setup, verify, bypass)
* Password changes/resets
* Account lockouts

**Session Events:**
* Session creation
* Session revocation
* Session expiration
* Concurrent session detection

**Account Events:**
* Account creation
* Account deactivation
* Account deletion
* Account restoration
* Email verification
* Profile changes

**Security Events:**
* Device trust/untrust
* Suspicious activity detection
* Rate limit violations
* Authorization failures

**Implementation:**

```python
class AuditLogService:
    @staticmethod
    async def log_event(
        user_id: Optional[UUID],
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        success: bool = True
    ) -> UUID:
        """Log security event."""
        
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            metadata=metadata or {},
        )
        
        await db.add(audit_log)
        await db.commit()
        
        return audit_log.id
```

### Log Retention

**✅ Do:**
* Retain logs for 90+ days (compliance)
* Archive old logs (S3, etc.)
* Implement log rotation
* Monitor log volume

**❌ Don't:**
* Log sensitive data (passwords, tokens, PII)
* Delete logs prematurely
* Allow log tampering

---

## Data Privacy

### GDPR Compliance

**Right to Access:**
```python
async def export_user_data(user_id: UUID) -> dict:
    """Export all user data (GDPR)."""
    
    user = await get_user(user_id)
    sessions = await get_user_sessions(user_id)
    audit_logs = await get_user_audit_logs(user_id)
    
    # Sanitize sensitive data
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
            # ... other non-sensitive fields
        },
        "sessions": [
            {
                "id": str(s.id),
                "created_at": s.created_at.isoformat(),
                "ip_address": s.ip_address,
                # ... sanitized session data
            }
            for s in sessions
        ],
        "audit_logs": [
            {
                "event_type": log.event_type,
                "timestamp": log.timestamp.isoformat(),
                # ... sanitized log data
            }
            for log in audit_logs
        ]
    }
```

**Right to Erasure:**
```python
async def delete_user_data(user_id: UUID):
    """Permanently delete user data."""
    
    # Mark account as deleted
    user = await get_user(user_id)
    user.deleted_at = datetime.now(timezone.utc)
    user.email = f"deleted_{user.id}@deleted.com"  # Anonymize
    user.full_name = "Deleted User"
    
    # Revoke all sessions
    await revoke_all_user_sessions(user_id)
    
    # Delete personal data
    await db.execute(
        delete(TrustedDevice).where(TrustedDevice.user_id == user_id)
    )
    await db.execute(
        delete(MFARecoveryCode).where(MFARecoveryCode.user_id == user_id)
    )
    
    # Keep audit logs (compliance requirement)
    # But anonymize identifiable information
    await db.execute(
        update(AuditLog)
        .where(AuditLog.user_id == user_id)
        .values(metadata={"anonymized": True})
    )
    
    await db.commit()
```

---

## API Security

### Input Validation

**✅ Do:**
* Validate all inputs
* Sanitize user data
* Use Pydantic models
* Implement input length limits

**❌ Don't:**
* Trust client-provided data
* Skip validation on "internal" endpoints
* Use string concatenation for SQL

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.markai.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### Security Headers

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## Incident Response

### Breach Detection

**Indicators:**
* Sudden spike in failed logins
* Multiple account lockouts
* Unusual access patterns
* Mass password resets
* Geographic anomalies

### Response Procedure

1. **Detect & Verify**
   * Confirm the incident
   * Assess scope and impact
   * Preserve evidence

2. **Contain**
   * Revoke affected sessions
   * Reset affected passwords
   * Block malicious IPs
   * Enable additional security measures

3. **Eradicate**
   * Remove attacker access
   * Patch vulnerabilities
   * Update security controls

4. **Recover**
   * Restore normal operations
   * Monitor for re-occurrence
   * Verify security posture

5. **Post-Incident**
   * Document incident
   * Update security policies
   * Train team on lessons learned

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Security Contact**: security@markai.com
