# Sprint 8.3.1: Authentication Lifecycle Hardening
## API Reference Guide

**Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Base URL**: `/api/v1`

---

## Table of Contents

1. [Session Management](#session-management)
2. [Auth Lifecycle](#auth-lifecycle)
3. [Account Lifecycle](#account-lifecycle)
4. [Device Trust](#device-trust)
5. [MFA Recovery](#mfa-recovery)
6. [Audit Logs](#audit-logs)
7. [Error Codes](#error-codes)
8. [Rate Limits](#rate-limits)

---

## Session Management

### List User Sessions

**Endpoint**: `GET /auth/sessions`  
**Auth Required**: Yes  
**Description**: Retrieve all active sessions for the authenticated user.

**Response**:
```json
{
  "sessions": [
    {
      "id": "uuid",
      "created_at": "2026-05-21T10:00:00Z",
      "last_active_at": "2026-05-21T12:00:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "device_info": {
        "type": "desktop",
        "os": "Windows 11"
      },
      "is_current": true,
      "is_active": true
    }
  ],
  "total": 3
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

### Revoke Specific Session

**Endpoint**: `DELETE /auth/sessions/{session_id}`  
**Auth Required**: Yes  
**Description**: Revoke a specific session by ID.

**Path Parameters**:
* `session_id` (UUID, required): The session ID to revoke

**Response**:
```json
{
  "message": "Session revoked successfully",
  "session_id": "uuid"
}
```

**Status Codes**:
* `204`: Session revoked successfully
* `401`: Unauthorized
* `403`: Forbidden (cannot revoke another user's session)
* `404`: Session not found

---

### Revoke All Sessions

**Endpoint**: `DELETE /auth/sessions/all`  
**Auth Required**: Yes  
**Description**: Revoke all user sessions except the current one.

**Query Parameters**:
* `except_current` (boolean, optional): Keep current session active (default: true)

**Response**:
```json
{
  "message": "All sessions revoked",
  "revoked_count": 5,
  "current_session_preserved": true
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

## Auth Lifecycle

### Request Password Reset

**Endpoint**: `POST /auth/password-reset/request`  
**Auth Required**: No  
**Description**: Request a password reset token.

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response**:
```json
{
  "message": "If this email exists, a reset link has been sent"
}
```

**Status Codes**:
* `200`: Request processed (always returns 200 to prevent email enumeration)

---

### Verify Reset Token

**Endpoint**: `POST /auth/password-reset/verify`  
**Auth Required**: No  
**Description**: Verify if a reset token is valid.

**Request Body**:
```json
{
  "token": "reset-token-string"
}
```

**Response**:
```json
{
  "valid": true,
  "expires_at": "2026-05-22T10:00:00Z"
}
```

**Status Codes**:
* `200`: Token is valid
* `400`: Token expired or invalid

---

### Reset Password

**Endpoint**: `POST /auth/password-reset/reset`  
**Auth Required**: No  
**Description**: Reset password using valid token.

**Request Body**:
```json
{
  "token": "reset-token-string",
  "new_password": "NewSecurePassword123!"
}
```

**Response**:
```json
{
  "message": "Password reset successfully",
  "user_id": "uuid"
}
```

**Status Codes**:
* `200`: Password reset successfully
* `400`: Invalid token or weak password

---

### Change Password (Authenticated)

**Endpoint**: `POST /auth/password/change`  
**Auth Required**: Yes  
**Description**: Change password for authenticated user.

**Request Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword123!"
}
```

**Response**:
```json
{
  "message": "Password changed successfully",
  "sessions_revoked": 4
}
```

**Status Codes**:
* `200`: Success
* `400`: Invalid current password or weak new password
* `401`: Unauthorized

---

### Request Email Verification

**Endpoint**: `POST /auth/email-verification/request`  
**Auth Required**: Yes  
**Description**: Request a new email verification token.

**Response**:
```json
{
  "message": "Verification email sent",
  "expires_at": "2026-05-22T10:00:00Z"
}
```

**Status Codes**:
* `200`: Verification email sent
* `400`: Email already verified
* `401`: Unauthorized
* `429`: Too many requests

---

### Verify Email

**Endpoint**: `POST /auth/email-verification/verify`  
**Auth Required**: No  
**Description**: Verify email address using token.

**Request Body**:
```json
{
  "token": "verification-token"
}
```

**Response**:
```json
{
  "message": "Email verified successfully",
  "user_id": "uuid",
  "verified_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Email verified
* `400`: Invalid or expired token

---

## Account Lifecycle

### Deactivate Account

**Endpoint**: `POST /account/lifecycle/deactivate`  
**Auth Required**: Yes  
**Description**: Deactivate user account (reversible).

**Request Body**:
```json
{
  "reason": "Taking a break"
}
```

**Response**:
```json
{
  "message": "Account deactivated",
  "deactivated_at": "2026-05-21T12:00:00Z",
  "can_reactivate": true
}
```

**Status Codes**:
* `200`: Account deactivated
* `401`: Unauthorized

---

### Reactivate Account

**Endpoint**: `POST /account/lifecycle/reactivate`  
**Auth Required**: No (uses email)
**Description**: Reactivate a deactivated account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "UserPassword123!"
}
```

**Response**:
```json
{
  "message": "Account reactivated",
  "reactivated_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Account reactivated
* `400`: Account not deactivated or credentials invalid

---

### Request Account Deletion

**Endpoint**: `POST /account/lifecycle/request-deletion`  
**Auth Required**: Yes  
**Description**: Request account deletion with grace period.

**Request Body**:
```json
{
  "reason": "No longer need the service",
  "password": "UserPassword123!"
}
```

**Response**:
```json
{
  "message": "Deletion scheduled",
  "scheduled_deletion_at": "2026-05-28T12:00:00Z",
  "grace_period_days": 7,
  "can_cancel_until": "2026-05-28T11:59:59Z"
}
```

**Status Codes**:
* `200`: Deletion scheduled
* `400`: Invalid password
* `401`: Unauthorized

---

### Cancel Account Deletion

**Endpoint**: `POST /account/lifecycle/cancel-deletion`  
**Auth Required**: Yes  
**Description**: Cancel scheduled account deletion.

**Response**:
```json
{
  "message": "Deletion canceled",
  "canceled_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Deletion canceled
* `400`: No deletion scheduled or grace period expired
* `401`: Unauthorized

---

### Confirm Immediate Deletion

**Endpoint**: `POST /account/lifecycle/confirm-deletion`  
**Auth Required**: Yes  
**Description**: Immediately delete account (skips grace period).

**Request Body**:
```json
{
  "password": "UserPassword123!",
  "confirmation": "DELETE MY ACCOUNT"
}
```

**Response**:
```json
{
  "message": "Account deleted",
  "deleted_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Account deleted
* `400`: Invalid password or confirmation
* `401`: Unauthorized

---

### Get Lifecycle Status

**Endpoint**: `GET /account/lifecycle/status`  
**Auth Required**: Yes  
**Description**: Get current account lifecycle status.

**Response**:
```json
{
  "is_active": true,
  "is_verified": true,
  "deactivated_at": null,
  "deletion_scheduled": false,
  "scheduled_deletion_at": null,
  "days_until_deletion": null
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

### Export User Data (GDPR)

**Endpoint**: `GET /account/lifecycle/data-export`  
**Auth Required**: Yes  
**Description**: Export all user data (GDPR compliance).

**Query Parameters**:
* `format` (string, optional): Export format - `json` or `csv` (default: `json`)

**Response** (JSON format):
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "sessions": [...],
  "audit_logs": [...],
  "exported_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Export successful
* `401`: Unauthorized

---

## Device Trust

### Trust Device

**Endpoint**: `POST /security/devices/trust`  
**Auth Required**: Yes  
**Description**: Mark current device as trusted.

**Request Body**:
```json
{
  "device_name": "My Laptop",
  "device_fingerprint": "sha256-hash",
  "trust_duration_days": 30
}
```

**Response**:
```json
{
  "device_id": "uuid",
  "device_name": "My Laptop",
  "trusted_at": "2026-05-21T12:00:00Z",
  "expires_at": "2026-06-20T12:00:00Z",
  "trusted": true
}
```

**Status Codes**:
* `200`: Device trusted
* `401`: Unauthorized

---

### List Trusted Devices

**Endpoint**: `GET /security/devices/trusted`  
**Auth Required**: Yes  
**Description**: List all trusted devices for user.

**Response**:
```json
{
  "devices": [
    {
      "id": "uuid",
      "device_name": "My Laptop",
      "device_fingerprint": "sha256-hash",
      "trusted_at": "2026-05-21T12:00:00Z",
      "last_used_at": "2026-05-21T12:00:00Z",
      "expires_at": "2026-06-20T12:00:00Z",
      "is_active": true
    }
  ],
  "total": 3
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

### Revoke Trusted Device

**Endpoint**: `DELETE /security/devices/trusted/{device_id}`  
**Auth Required**: Yes  
**Description**: Revoke trust for specific device.

**Path Parameters**:
* `device_id` (UUID, required): Device ID to revoke

**Response**:
```json
{
  "message": "Device trust revoked",
  "device_id": "uuid"
}
```

**Status Codes**:
* `204`: Device trust revoked
* `401`: Unauthorized
* `404`: Device not found

---

### Revoke All Trusted Devices

**Endpoint**: `DELETE /security/devices/trusted/all`  
**Auth Required**: Yes  
**Description**: Revoke trust for all devices.

**Response**:
```json
{
  "message": "All device trusts revoked",
  "revoked_count": 5
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

## MFA Recovery

### Generate Recovery Codes

**Endpoint**: `POST /security/mfa/recovery/generate`  
**Auth Required**: Yes  
**Description**: Generate new MFA recovery codes.

**Request Body**:
```json
{
  "count": 10
}
```

**Response**:
```json
{
  "codes": [
    "ABCD-1234-EFGH",
    "IJKL-5678-MNOP",
    ...
  ],
  "generated_at": "2026-05-21T12:00:00Z",
  "warning": "Store these codes securely. Each can only be used once."
}
```

**Status Codes**:
* `200`: Codes generated
* `401`: Unauthorized

---

### Verify Recovery Code

**Endpoint**: `POST /security/mfa/recovery/verify`  
**Auth Required**: Yes  
**Description**: Verify and consume a recovery code.

**Request Body**:
```json
{
  "code": "ABCD-1234-EFGH"
}
```

**Response**:
```json
{
  "valid": true,
  "remaining_codes": 9,
  "used_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Code is valid
* `400`: Code invalid or already used
* `401`: Unauthorized

---

### Check Recovery Code Status

**Endpoint**: `GET /security/mfa/recovery/status`  
**Auth Required**: Yes  
**Description**: Check recovery code status.

**Response**:
```json
{
  "has_codes": true,
  "total_codes": 10,
  "used_codes": 1,
  "remaining_codes": 9,
  "generated_at": "2026-05-21T12:00:00Z"
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

### Regenerate Recovery Codes

**Endpoint**: `POST /security/mfa/recovery/regenerate`  
**Auth Required**: Yes  
**Description**: Regenerate recovery codes (invalidates old codes).

**Request Body**:
```json
{
  "count": 10
}
```

**Response**:
```json
{
  "codes": [...],
  "generated_at": "2026-05-21T12:00:00Z",
  "previous_codes_invalidated": true
}
```

**Status Codes**:
* `200`: Codes regenerated
* `401`: Unauthorized

---

## Audit Logs

### Get Audit Logs

**Endpoint**: `GET /security/audit/logs`  
**Auth Required**: Yes  
**Description**: Retrieve user's audit logs.

**Query Parameters**:
* `event_type` (string, optional): Filter by event type
* `start_date` (ISO 8601, optional): Start date filter
* `end_date` (ISO 8601, optional): End date filter
* `limit` (integer, optional): Number of records (default: 50, max: 1000)
* `offset` (integer, optional): Pagination offset

**Response**:
```json
{
  "logs": [
    {
      "id": "uuid",
      "event_type": "login",
      "timestamp": "2026-05-21T12:00:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "metadata": {}
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Status Codes**:
* `200`: Success
* `401`: Unauthorized

---

### Export Audit Logs

**Endpoint**: `GET /security/audit/logs/export`  
**Auth Required**: Yes  
**Description**: Export audit logs.

**Query Parameters**:
* `format` (string, required): Export format - `json` or `csv`
* `start_date` (ISO 8601, optional): Start date filter
* `end_date` (ISO 8601, optional): End date filter

**Response**: File download (JSON or CSV)

**Status Codes**:
* `200`: Export successful
* `401`: Unauthorized

---

### Admin Get User Logs

**Endpoint**: `GET /security/audit/admin/logs/{user_id}`  
**Auth Required**: Yes (Admin only)  
**Description**: Retrieve audit logs for any user.

**Path Parameters**:
* `user_id` (UUID, required): Target user ID

**Query Parameters**: Same as regular logs endpoint

**Response**: Same as regular logs endpoint

**Status Codes**:
* `200`: Success
* `401`: Unauthorized
* `403`: Forbidden (not admin)

---

## Error Codes

### Standard Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-05-21T12:00:00Z",
  "path": "/api/v1/auth/login"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `INVALID_CREDENTIALS` | Invalid email or password |
| `ACCOUNT_LOCKED` | Account temporarily locked |
| `ACCOUNT_DEACTIVATED` | Account is deactivated |
| `ACCOUNT_DELETED` | Account has been deleted |
| `TOKEN_EXPIRED` | Token has expired |
| `TOKEN_INVALID` | Token is invalid |
| `WEAK_PASSWORD` | Password doesn't meet requirements |
| `EMAIL_NOT_VERIFIED` | Email verification required |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `DEVICE_NOT_TRUSTED` | Device trust required |
| `MFA_REQUIRED` | MFA verification required |

---

## Rate Limits

### Per-Endpoint Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 attempts | 15 minutes |
| `/auth/register` | 3 attempts | 1 hour |
| `/auth/password-reset/request` | 3 attempts | 1 hour |
| `/auth/mfa/verify` | 5 attempts | 15 minutes |
| `/auth/email-verification/request` | 3 attempts | 1 hour |

### Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1716297600
```

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the `/auth/login` endpoint and are valid for 24 hours.

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Contact**: engineering@markai.com
