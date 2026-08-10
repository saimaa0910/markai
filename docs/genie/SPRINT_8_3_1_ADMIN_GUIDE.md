# Sprint 8.3.1: Authentication Lifecycle
## Administrator Guide

**Version**: 1.0.0  
**Audience**: System Administrators  
**Last Updated**: 2026-05-21

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Migration](#installation--migration)
3. [Configuration](#configuration)
4. [User Management](#user-management)
5. [Security Monitoring](#security-monitoring)
6. [Audit & Compliance](#audit--compliance)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)
9. [API Administration](#api-administration)

---

## Overview

### New Features in Sprint 8.3.1

This release introduces enterprise-grade authentication lifecycle management:

**Phase 1: Session Management**
* Comprehensive session tracking and control
* Multi-device session management
* Real-time session revocation
* Session metadata enrichment

**Phase 2: Auth Lifecycle**
* Enhanced password reset workflow
* Email verification improvements
* Account lockout protection
* Failed login tracking

**Phase 3: Account Lifecycle**
* Self-service account deactivation
* Scheduled account deletion with grace period
* GDPR-compliant data export
* Privacy dashboard

**Phase 4: Security Hardening**
* Trusted device management
* MFA recovery codes
* Database-backed rate limiting
* Comprehensive audit logging

### System Requirements

* **Database**: PostgreSQL 13+ or MySQL 8+
* **Python**: 3.10+
* **Redis**: 6+ (optional, for distributed rate limiting)
* **Email Service**: SMTP server or provider (SendGrid, SES, etc.)

---

## Installation & Migration

### Step 1: Backup Database

```bash
# PostgreSQL
pg_dump -U username -d eaimos > backup_pre_8_3_1.sql

# MySQL
mysqldump -u username -p eaimos > backup_pre_8_3_1.sql
```

### Step 2: Update Dependencies

```bash
cd /path/to/markai/apps/api
pip install -r requirements.txt
```

### Step 3: Run Migrations

```bash
# Check current migration status
alembic current

# Review pending migrations
alembic history

# Apply all Sprint 8.3.1 migrations
alembic upgrade head

# Verify migration success
alembic current
```

**Expected migrations:**
* `a8b9c1d2e3f4_sprint_8_3_1_auth_hardening.py` (Phase 1)
* `b1c2d3e4f5g6_sprint_8_3_1_phase_2_auth_lifecycle.py` (Phase 2)
* `c2d3e4f5g6h7_sprint_8_3_1_phase_3_account_lifecycle.py` (Phase 3)
* `d3e4f5g6h7i8_sprint_8_3_1_phase_4_security_hardening.py` (Phase 4)

### Step 4: Verify Database Changes

```sql
-- Verify new tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('trusted_devices', 'mfa_recovery_codes', 'rate_limit_logs', 'audit_logs');

-- Verify new user fields
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN (
  'change_password_required',
  'temporary_password',
  'mfa_recovery_codes_generated_at',
  'trusted_devices_enabled',
  'deletion_requested_at'
);
```

### Step 5: Update Environment Configuration

Add these to your `.env` file:

```env
# Session Management
SESSION_MAX_LIFETIME_DAYS=7
SESSION_CLEANUP_INTERVAL_HOURS=24

# Account Lockout
MAX_FAILED_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Account Deletion
DELETION_GRACE_PERIOD_DAYS=7

# Trusted Devices
DEFAULT_DEVICE_TRUST_DURATION_DAYS=30

# MFA Recovery
DEFAULT_RECOVERY_CODES_COUNT=10

# Rate Limiting
RATE_LIMIT_LOGIN_MAX=5
RATE_LIMIT_LOGIN_WINDOW_SECONDS=900
RATE_LIMIT_REGISTER_MAX=3
RATE_LIMIT_REGISTER_WINDOW_SECONDS=3600

# Audit Logging
AUDIT_LOG_RETENTION_DAYS=90
```

### Step 6: Restart Application

```bash
# Systemd
sudo systemctl restart eaimos-api

# Docker
docker-compose restart api

# Manual
pkill -f "uvicorn api.main:app"
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Step 7: Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Test new endpoints
curl http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer <token>"
```

---

## Configuration

### Session Configuration

**Config location**: `api/core/config.py`

```python
class Settings(BaseSettings):
    # Session settings
    SESSION_MAX_LIFETIME_DAYS: int = 7
    SESSION_IDLE_TIMEOUT_HOURS: int = 24
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24
    ENABLE_SESSION_TRACKING: bool = True
    ENABLE_DEVICE_FINGERPRINTING: bool = True
```

**Database cleanup job** (recommended - cron):

```bash
# Add to crontab
0 2 * * * /path/to/python /path/to/api/scripts/cleanup_sessions.py
```

### Account Lockout Configuration

```python
class Settings(BaseSettings):
    # Lockout settings
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    ENABLE_LOCKOUT_NOTIFICATIONS: bool = True
```

**Admin override**: Admins can unlock accounts anytime via:

```bash
curl -X POST http://localhost:8000/api/v1/account/lifecycle/admin/unlock/{user_id} \
  -H "Authorization: Bearer <admin_token>"
```

### Trusted Device Configuration

```python
class Settings(BaseSettings):
    # Trusted device settings
    ENABLE_TRUSTED_DEVICES: bool = True
    DEFAULT_DEVICE_TRUST_DURATION_DAYS: int = 30
    MAX_TRUSTED_DEVICES_PER_USER: int = 10
    DEVICE_FINGERPRINT_ALGORITHM: str = "sha256"
```

### Rate Limiting Configuration

**Per-endpoint limits** in `api/middleware/rate_limiting.py`:

```python
RATE_LIMIT_CONFIG = {
    "/auth/login": {
        "max_attempts": 5,
        "window_seconds": 900,  # 15 minutes
    },
    "/auth/register": {
        "max_attempts": 3,
        "window_seconds": 3600,  # 1 hour
    },
    "/auth/password-reset/request": {
        "max_attempts": 3,
        "window_seconds": 3600,
    },
}
```

**Using Redis for distributed rate limiting:**

```env
REDIS_URL=redis://localhost:6379/0
ENABLE_REDIS_RATE_LIMITING=true
```

### Audit Logging Configuration

```python
class Settings(BaseSettings):
    # Audit settings
    ENABLE_AUDIT_LOGGING: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90
    AUDIT_LOG_SENSITIVE_DATA: bool = False  # PII in logs
```

**Automatic cleanup job**:

```bash
# Cron job to clean old audit logs
0 3 * * * /path/to/python /path/to/api/scripts/cleanup_audit_logs.py
```

---

## User Management

### Admin Operations

#### Unlock User Account

```bash
curl -X POST http://localhost:8000/api/v1/account/lifecycle/admin/unlock/{user_id} \
  -H "Authorization: Bearer <admin_token>"
```

#### Deactivate User Account

```bash
curl -X POST http://localhost:8000/api/v1/account/lifecycle/admin/deactivate/{user_id} \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Policy violation",
    "notify_user": true
  }'
```

#### Force Password Change

```bash
curl -X POST http://localhost:8000/api/v1/account/lifecycle/admin/force-password-change/{user_id} \
  -H "Authorization: Bearer <admin_token>"
```

#### Reset User MFA

```bash
curl -X POST http://localhost:8000/api/v1/security/admin/reset-mfa/{user_id} \
  -H "Authorization: Bearer <admin_token>"
```

#### Revoke All User Sessions

```bash
curl -X DELETE http://localhost:8000/api/v1/auth/sessions/admin/{user_id}/all \
  -H "Authorization: Bearer <admin_token>"
```

### Bulk Operations

#### Export All Users

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/export?format=csv" \
  -H "Authorization: Bearer <admin_token>" \
  -o users_export.csv
```

#### Bulk Password Reset

```python
# Script: bulk_password_reset.py
import requests

user_ids = ["uuid1", "uuid2", "uuid3"]
for user_id in user_ids:
    response = requests.post(
        f"http://localhost:8000/api/v1/account/lifecycle/admin/force-password-change/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    print(f"User {user_id}: {response.status_code}")
```

---

## Security Monitoring

### Dashboard Metrics

**Key metrics to monitor:**

1. **Failed Login Attempts**
   * High rate indicates brute-force attack
   * Check `/security/audit/logs?event_type=login_failed`

2. **Account Lockouts**
   * Spike may indicate attack or user confusion
   * Check `/security/audit/logs?event_type=account_locked`

3. **Active Sessions**
   * Unusual growth may indicate token leak
   * Query database: `SELECT COUNT(*) FROM sessions WHERE is_active = true`

4. **MFA Bypass Attempts**
   * Recovery code usage spikes
   * Check `/security/audit/logs?event_type=mfa_recovery_used`

5. **Password Resets**
   * High volume may indicate phishing campaign
   * Check `/security/audit/logs?event_type=password_reset`

### Monitoring Queries

```sql
-- Failed logins in last hour
SELECT user_id, COUNT(*) as attempts
FROM audit_logs
WHERE event_type = 'login_failed'
AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) > 5
ORDER BY attempts DESC;

-- Locked accounts
SELECT id, email, locked_until
FROM users
WHERE locked_until > NOW()
ORDER BY locked_until DESC;

-- Active sessions per user
SELECT user_id, COUNT(*) as session_count
FROM sessions
WHERE is_active = true
GROUP BY user_id
HAVING COUNT(*) > 5
ORDER BY session_count DESC;
```

### Security Alerts

**Configure alerts for:**

1. **Brute Force Detection**
   ```sql
   -- Alert if >10 failed logins from same IP in 5 minutes
   SELECT ip_address, COUNT(*) 
   FROM audit_logs
   WHERE event_type = 'login_failed'
   AND created_at > NOW() - INTERVAL '5 minutes'
   GROUP BY ip_address
   HAVING COUNT(*) > 10;
   ```

2. **Account Takeover Indicators**
   * Login from new country
   * Multiple devices in short time
   * Suspicious session patterns

3. **MFA Issues**
   * Repeated MFA failures
   * Multiple recovery code uses
   * MFA disable attempts

---

## Audit & Compliance

### GDPR Compliance

**Right to Access:**
* Users can export their data via `/account/lifecycle/data-export`
* Format: JSON or CSV
* Includes all personal data

**Right to Erasure:**
* Users can delete accounts via `/account/lifecycle/request-deletion`
* 7-day grace period (configurable)
* Hard delete after grace period

**Audit Trail:**
* All actions logged in `audit_logs` table
* Retained for 90 days (configurable)
* Exportable for compliance audits

### Compliance Reports

```bash
# Generate compliance report
curl -X GET "http://localhost:8000/api/v1/admin/compliance/report?start_date=2026-01-01&end_date=2026-12-31" \
  -H "Authorization: Bearer <admin_token>" \
  -o compliance_report_2026.pdf
```

**Report includes:**
* Total user accounts
* Active vs. inactive accounts
* Deletion requests processed
* Data export requests
* Security incidents
* Average password age
* MFA adoption rate

### Audit Log Retention

**Manual cleanup:**

```sql
-- Delete logs older than 90 days
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '90 days';
```

**Automated cleanup script:**

```python
# scripts/cleanup_audit_logs.py
import asyncio
from api.services.audit_log_service import AuditLogService
from api.core.config import settings

async def cleanup():
    deleted_count = await AuditLogService.cleanup_old_logs(
        retention_days=settings.AUDIT_LOG_RETENTION_DAYS
    )
    print(f"Deleted {deleted_count} old audit logs")

if __name__ == "__main__":
    asyncio.run(cleanup())
```

---

## Troubleshooting

### Issue: Users Can't Log In

**Check:**
1. Account lockout: `SELECT locked_until FROM users WHERE email = 'user@example.com'`
2. Account deactivated: `SELECT is_active FROM users WHERE email = 'user@example.com'`
3. Email not verified: `SELECT is_verified FROM users WHERE email = 'user@example.com'`
4. Rate limiting: Check `rate_limit_logs` table

**Fix:**
```sql
-- Unlock account
UPDATE users 
SET locked_until = NULL, failed_login_count = 0 
WHERE email = 'user@example.com';

-- Reactivate account
UPDATE users 
SET is_active = true, deactivated_at = NULL 
WHERE email = 'user@example.com';
```

### Issue: High Failed Login Rate

**Investigation:**
```sql
-- Top IPs with failed logins
SELECT ip_address, COUNT(*) as attempts
FROM audit_logs
WHERE event_type = 'login_failed'
AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
ORDER BY attempts DESC
LIMIT 20;
```

**Mitigation:**
1. Block IPs at firewall level
2. Reduce rate limits temporarily
3. Enable CAPTCHA for login
4. Notify affected users

### Issue: Session Cleanup Not Running

**Check:**
```sql
-- Count expired sessions
SELECT COUNT(*) 
FROM sessions 
WHERE expires_at < NOW() AND is_active = true;
```

**Manual cleanup:**
```sql
-- Clean expired sessions
UPDATE sessions 
SET is_active = false, revoked_at = NOW() 
WHERE expires_at < NOW() AND is_active = true;
```

**Fix cron job:**
```bash
# Verify cron is running
sudo systemctl status cron

# Check cron logs
grep "cleanup_sessions" /var/log/syslog
```

---

## Maintenance

### Daily Tasks

* Monitor failed login rates
* Check for locked accounts
* Review security alerts

### Weekly Tasks

* Review audit logs for anomalies
* Check session counts per user
* Verify backup success
* Update rate limit rules if needed

### Monthly Tasks

* Generate compliance reports
* Review and update security policies
* Analyze MFA adoption rate
* Clean up old audit logs
* Test disaster recovery

### Quarterly Tasks

* Security audit
* Performance tuning
* Update dependencies
* Review and update documentation

---

## API Administration

### Admin Endpoints

All admin endpoints require `is_superuser = true`.

**Base path**: `/api/v1/admin`

* `GET /admin/users` - List all users
* `GET /admin/users/{user_id}` - Get user details
* `POST /admin/users/{user_id}/unlock` - Unlock account
* `POST /admin/users/{user_id}/deactivate` - Deactivate account
* `DELETE /admin/users/{user_id}/sessions` - Revoke all sessions
* `POST /admin/users/{user_id}/reset-mfa` - Reset MFA
* `GET /admin/audit/logs` - Get all audit logs
* `GET /admin/compliance/report` - Generate compliance report

### API Rate Limits (Admin)

Admin endpoints have higher rate limits:

* 100 requests per minute per admin
* 1000 requests per hour per admin

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Support**: devops@markai.com
