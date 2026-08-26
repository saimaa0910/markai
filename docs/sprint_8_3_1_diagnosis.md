# Sprint 8.3.1 Auth Hardening — Test Failure Diagnosis Report

- **Date:** 2026-08-11
- **Scope:** `apps/api` test suite (auth hardening sprint)
- **Result:** 59 failed, 7 errors, 43 passed (~64 s run)
- **Status:** Diagnosis only — no code changes made

---

## Executive Summary

The Sprint 8.3.1 (authentication hardening) work landed in a half-integrated state. The
migration chain is linear and healthy (`d3e4f5g6h7i8` is the single head), but the
implementation contains:

1. A one-line import bug that crashes the `UserSession` model (cascades to most session tests).
2. A column-name mismatch between the model and the session routes (500 on list-sessions).
3. A typo'd module import in the audit log service.
4. Migrations that create tables without the standard `Base` columns the models require.
5. A large contract mismatch: Sprint 8.3.1 tests call services with a simple
   `db=`/kwargs interface, while production services are DDD-style
   (`ServiceContext` + DTOs + Unit-of-Work).
6. Feature gaps: account restore path, MFA-recovery-code generation precondition, and
   older tests that are stale relative to *intended* new behavior.

The root-cause clusters and exact file/line references follow.

---

## Blocker 1 — `timezone` NameError in `UserSession` model

- **File:** `apps/api/src/api/models/iam.py:334`
- **Failure:** `NameError: name 'timezone' is not defined`
- **Cause:** `iam.py:28` imports only `from datetime import datetime`, but
  `UserSession.last_active_at` uses `datetime.now(timezone.utc)` as its default.
- **Impact:** 7 pytest setup errors + any session insert/query in tests. This is the
  single highest-leverage fix.
- **Fix:** change import to `from datetime import datetime, timezone`.

---

## Blocker 2 — `last_activity_at` vs `last_active_at` mismatch

- **File:** `apps/api/src/api/routes/auth_session.py:127`
- **Failure:** `AttributeError: type object 'UserSession' has no attribute 'last_activity_at'. Did you mean: 'last_active_at'?` → HTTP 500.
- **Cause:** Model column is `last_active_at` (`models/iam.py:332`); the route sorts and
  serializes by `last_activity_at`.
- **Impact:** `GET /auth/sessions` fails. `test_security_hardening.py:264,307` and
  `test_session_management.py` sessions-listing tests fail.
- **Fix:** reconcile the name across the route and the response schema (the public API
  field name is `last_activity_at`; the model/DB column is `last_active_at` — decide one
  canonical name and map accordingly).

---

## Blocker 3 — dead import in audit log service

- **File:** `apps/api/src/api/services/audit_log_service.py:54,97,149,189,219`
- **Failure:** `ModuleNotFoundError: No module named 'api.models.audit'`
- **Cause:** `AuditLog` actually lives in `api.models.platform_events` and is re-exported
  from `api.models.auth`. The top-level service imports the wrong module name (typo).
- **Note:** there are two audit log services — `services/audit_log_service.py`
  (broken import) and `services/core/audit_log_service.py` (different implementation).
  The tests import `from api.services.audit_log_service import AuditLogService`.
- **Fix:** change all five `from api.models.audit import AuditLog` to
  `from api.models.platform_events import AuditLog`.

---

## Blocker 4 — migrations missing standard `Base` columns

- **File:** `apps/api/alembic/versions/d3e4f5g6h7i8_sprint_8_3_1_phase_4_security_hardening.py`
- **Failure:** `asyncpg.exceptions.UndefinedColumnError: column "deleted_at" of relation "trusted_devices" does not exist`
- **Cause:** Every model inherits from `Base` (`apps/api/src/api/database/base.py`), which
  adds `id`, `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`,
  `version`. The Phase 4 migration creates `trusted_devices`, `mfa_recovery_codes`, and
  `rate_limit_log` **without** `deleted_at`, `created_by`, `updated_by`, or `version`.
- **Impact:** any SELECT/UPDATE on these tables references missing columns.
- **Fix:** add the missing columns to the migrations (Phase 4 and audit Phase 1–3
  migrations for the same pattern). Prefer `add_column` with `nullable` defaults so
  existing databases can upgrade in place.

---

## Blocker 5 — tests vs services contract mismatch

Production services are DDD-style (`ServiceContext` + DTOs + UoW + repositories). The
Sprint 8.3.1 tests call them with a plain `db=`/kwargs interface.

| Test call (as written) | Production signature | Location |
|---|---|---|
| `SessionService.create_session(db=...)` | `create_session(ctx, dto)` | `services/iam/session_service.py:93` |
| `AccountLifecycleService.deactivate_account(db=...)` | signature differs | `services/account_lifecycle_service.py:240` |
| `AccountLifecycleService.request_deletion` | does not exist | `services/account_lifecycle_service.py` |
| `AccountLifecycleService.export_user_data` | exists as `export_account_data` | `services/account_lifecycle_service.py:69` |
| `DeviceTrustService.trust_device(device_name=...)` | rejects `device_name` | `services/device_trust_service.py` |
| `MFARecoveryService.generate_recovery_codes(count=...)` | rejects `count` | `services/mfa_recovery_service.py:80` |
| `RateLimitService.check_rate_limit(max_attempts=...)` | rejects `max_attempts` | `services/rate_limit_service.py` |
| `AuditLogService.log_event(metadata=...)` | rejects `metadata` | `services/audit_log_service.py:35` |
| `PasswordResetToken(token=...)` / `EmailVerificationToken(token=...)` | models only store `token_hash` | `models/iam.py:446`, `models/email_verification.py:45` |

**Decision needed:** align tests to the production contracts (recommended — production
services are fully built and integrated), or change service signatures. The user wants all
features/services to work without errors.

---

## Blocker 6 — behavior/feature gaps

1. **MFA recovery codes require MFA enabled**
   - `services/mfa_recovery_service.py:112` raises
     `ValueError("MFA must be enabled before generating recovery codes")`.
   - Tests generate codes without enabling MFA first → must either enable MFA in the test
     setup or relax the precondition (product decision).

2. **Account restore incomplete** (`tests/test_account_lifecycle.py::TestAccountRestore`)
   - Restore path does not call `send_account_restored_email` (called 0 times).
   - "Cannot restore after 7-day window" not enforced.

3. **Stale older tests (intended behavior)**
   - `tests/test_auth.py` (7/8 failing): registers then logs in without email verification
     → blocked. This is **correct** new behavior (Phase 6: unverified users cannot log in);
     tests are stale and need to verify the email first.
   - `tests/test_phase2_auth_orgs.py` (2 failing): forgot/reset password + org management
     & invitations flows.
   - `tests/test_account_lifecycle.py` (3 failing): restore-cancels-deletion,
     restore-after-window-fails, restore-sends-confirmation-email.

4. **Email worker noise** — `eaimos.email.worker` logs "Email delivery returned False"
   during tests. Expected in the test env; not a real failure, but noisy.

---

## Recommended fix order

1. Blocker 1 — `timezone` import (unblocks ~14 session tests).
2. Blocker 3 — audit import typo (unblocks `TestAuditLogging` + `TestSecurityServices`).
3. Blocker 2 — session column-name reconciliation (unblocks session listing 500s).
4. Blocker 4 — migration column additions (unblocks `TestDeviceTrust` DB errors).
5. Blocker 5 — align tests to production service contracts (or decide per-service).
6. Blocker 6 — close feature gaps and update stale older tests.

---

## Appendix — failing test files (summary)

- `tests/sprint_8_3_1/test_session_management.py` — 7 failed + 7 errors (blockers 1, 2, 5)
- `tests/sprint_8_3_1/test_auth_lifecycle.py` — 13 failed (blockers 5, 6)
- `tests/sprint_8_3_1/test_account_lifecycle.py` — 19 failed (blockers 5, 6)
- `tests/sprint_8_3_1/test_security_hardening.py` — 20 failed (blockers 2, 3, 4, 5, 6)
- `tests/test_auth.py` — 7 failed (blocker 6, stale tests)
- `tests/test_phase2_auth_orgs.py` — 2 failed (blocker 6)
- `tests/test_account_lifecycle.py` — 3 failed (blocker 6)
