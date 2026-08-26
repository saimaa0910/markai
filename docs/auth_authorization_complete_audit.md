# EAIMOS — Authentication, Authorization & IAM: Complete Implementation Audit

**Sprint:** 8.3.1 (auth hardening) → readiness for Sprint 8.4 (auth/authorization/IAM hardening)
**Date:** 2026-08-11
**Type:** Pre-implementation audit (Phase 1 of Sprint 8.4) — no code changed
**Base paths:** backend `apps/api/src/api`, frontend `apps/web/src`

---

## 1. Executive Summary

EAIMOS has a **large, real IAM foundation**: a `UserSession` + JWT `jti` session model,
rotating refresh tokens with family IDs, hashed single-use email-verification and
password-reset tokens, Argon2id password hashing, TOTP MFA wired into login, lockout
tracking, org membership + RBAC roles, audit logging, and account lifecycle (deletion /
restore / export). **Do not rebuild this — it can be corrected.**

However, the implementation is in a **half-integrated state** with multiple competing
implementations, several **critical authorization vulnerabilities**, guaranteed-runtime
crash bugs, dead/unmounted routers, an unregistered rate limiter, and a frontend whose
API service layer calls many endpoints that do not exist. A prior test run recorded
**59 failed, 7 errors, 43 passed** (`docs/sprint_8_3_1_diagnosis.md`).

**Highest-severity findings (must fix before Sprint 8.4 completion):**
1. Any authenticated user can **list all users**, **modify any user (incl. `is_superuser`/password)**, and **hard-delete any user** — `routes/users.py`.
2. **IDOR** on admin account-lifecycle endpoints (unlock / export / status / history) — `routes/account_lifecycle.py`.
3. **Invitation authorization is broken**: accepting doesn't verify the token holder's email; rejecting requires **no authentication** at all — `routes/auth.py`.
4. **Logout does not revoke the active `UserSession`** (refresh tokens only) — Phase 2 acceptance criterion fails.
5. **Password reset revokes refresh tokens but not sessions** — Phase 3 partially fails.
6. **Refresh-token family reuse detection is not implemented** (`is_used` never read/written) — Phase 11 fails.
7. **Rate limiting is never registered**; config paths point at non-existent routes — Phase 13 fails.
8. **GDPR account export crashes** on non-existent model attributes — Phase 9 fails.
9. **3 of the 4 security-hardening routers are dead code** (imported, never mounted) — Phase 14 fails.
10. **Campaign email passes `Contact.id` as `User.id`** → silently delivers nothing — Phase 19.

---

## 2. Scope & Methodology

Audited (read-only): routers, dependencies, middleware, services, models, migrations,
Celery workers, email service, frontend auth pages/stores/API clients. Every finding below
was **verified by reading the code**; the original agent claims that contradicted the code
(e.g. `account_cleanup.py` referencing missing columns) were corrected. Line numbers are
accurate as of 2026-08-11.

---

## 3. Implementation Map

### 3.1 Router registration (`apps/api/src/api/main.py`)

| Router file | Mounted (main.py) | Live path(s) |
|---|---|---|
| `routes/auth.py` | ✅ :51 | `/api/v1/auth/*` (register, login, refresh, logout, logout-all, forgot/reset-password, verify-email, change-password, password-change, MFA, oauth, invitations) |
| `routes/auth_session.py` | ✅ :52 | `/api/v1/auth/sessions` (list, revoke, revoke-all) |
| `routes/auth_lifecycle.py` | ✅ :53 | `/api/v1/auth/*` (invitations resend, change-password, account/delete, account/restore) |
| `routes/account_lifecycle.py` | ✅ :54 | `/api/v1/account/lifecycle/*` |
| `routes/users.py` | ✅ :55 | `/api/v1/users/*` |
| `routes/organizations.py` | ✅ :56 | `/api/v1/organizations/*` (incl. invites, members, roles) |
| `routes/rbac.py` | ✅ :87 | `/api/v1/rbac/*` |
| `routes/audit.py` | ✅ :88 | `/api/v1/audit/*` |
| `routes/sessions.py` | ✅ :86 | `/api/v1/sessions/*` (second session router) |
| `routes/security.py` | ✅ :84 | `/api/v1/ai/security/*` |
| `routes/device_trust.py` | ❌ **never** | `/api/v1/security/devices/*` — **dead** |
| `routes/mfa_recovery.py` | ❌ **never** | `/api/v1/security/mfa/recovery/*` — **dead** |
| `routes/audit_logs.py` | ❌ **never** | `/api/v1/security/audit/*` — **dead** |

`main.py:11` imports `device_trust, mfa_recovery, audit_logs` but lines 51–88 never call
`include_router` for them.

### 3.2 Core auth flows — wiring state

| Flow | Route → Service → Model | Status |
|---|---|---|
| Register | `auth.py:595` → direct SQLAlchemy | 🟢 mostly (unverified users blocked at login — intended) |
| Login | `auth.py:719` → `store_refresh_token:316`, lockout `:418`, MFA `:761` | 🟢 core works |
| Refresh | `auth.py:817` → `rotate_refresh_token:374` | 🟠 **family reuse missing** |
| Logout | `auth.py:855` | 🔴 **does not revoke UserSession** |
| Logout-all | `auth.py:873` | 🟢 revokes tokens + sessions |
| Forgot password | `auth.py:912` → hashed DB token `:529` | 🟢 |
| Reset password | `auth.py:943` → consume `:559` | 🟠 **sessions not revoked** |
| Verify email | `auth.py:1002` → hashed DB token `:464` | 🟢 |
| Change password | `auth.py:1087` **and** `auth_lifecycle.py:197` | 🔴 duplicate + incomplete |
| MFA (TOTP) | `auth.py:1139–1347` (pyotp, recovery codes in preferences) | 🟢 wired into login |
| MFA recovery (table) | `mfa_recovery.py` + `mfa_recovery_service.py` | 🔴 dead duplicate |
| Device trust | `device_trust.py` + `device_trust_service.py` | 🔴 dead router |
| Account delete (7-day) | `users.py:373`, `auth_lifecycle.py:301` | 🟠 two divergent flows |
| Account restore | `auth.py:792`, `users.py:458`, `auth_lifecycle.py:368` | 🔴 three divergent flows |
| Account export | `account_lifecycle.py` → `account_lifecycle_service.py:69` | 🔴 crashes |
| Account unlock | `account_lifecycle.py:313` | 🔴 IDOR + dual fields |
| Invitation accept/reject | `auth.py:1588/1654` | 🔴 no identity binding / unauth reject |
| OAuth | `auth.py:1352` (google/github/microsoft/okta) | 🟢, mock bypass in dev/test |
| Admin user mgmt | `users.py:541–678` | 🟠 suspend/restore/reset gated; `users.py:277/349` **ungated** |

### 3.3 Models inventory

- **`models/user.py`** — identity, MFA (incl. `mfa_secret`), lockout (`failed_login_count`, `locked_until`, plus **duplicate** `is_locked`, `failed_login_attempts`), temp-password columns (`change_password_required`, `temporary_password`, `temporary_password_expires_at`), deletion lifecycle (`deletion_requested_at`, `scheduled_deletion_at`, `deletion_reason`), `metadata_json`, `preferences`.
- **`models/iam.py`** — `UserSession` (:236, `last_active_at`), `RefreshToken` (:357, `family_id`, `session_id`, `token_hash`, `is_revoked`, **`is_used` never used**), `PasswordResetToken` (:423), `Role`/`Permission`/`role_permissions_junction`/`UserRole` (:55–210), `ApiKey` (:474), OAuth (:555–597).
- **`models/security.py`** — `TrustedDevice` (:122), `MFARecoveryCode` (:182), `RateLimitLog` (:209) — tables created by migration `d3e4f5g6h7i8` **without** the `Base` columns `deleted_at`/`created_by`/`updated_by`/`version`.
- **`models/platform_events.py`** — `AuditLog` (:141, `actor_id`, `actor_email`, `actor_ip`, `actor_user_agent`, `entity_type`, `entity_id`, `action`, `description`, `risk_level`, …). **No** `user_id`/`ip_address`/`user_agent`/`metadata`.
- **`models/membership.py`** — `UserOrganization`, `OrganizationInvitation` (token stored hashed, `email`, `invited_by`, `role`, `expires_at`, `is_accepted/is_rejected`).

### 3.4 Frontend surface (`apps/web/src`)

**Auth pages present:** `login`, `register`, `forgot-password`, `reset-password`, `verify-email`, `invitation` (+ `invitation/[token]`), `restore-account`, `delete-account`.

**Missing pages:** change-password, MFA setup/verify, sessions list, roles/permissions, security settings, admin user management, email-change confirmation, `accept-invitation` (linked by `auth_lifecycle.py:164` but absent).

**Force-password-change handling:** only read in `app/auth/login/page.tsx:202,258` via `metadata_json?.change_password_required` — while backend enforcement reads the **explicit columns** (`middleware/auth_enforcement.py:154,165`). Frontend and backend disagree on where the flag lives.

**Auth state:** Zustand stores / API client in `apps/web/src/services/*` (`auth.service.ts`, `auth-session.service.ts`, `account-lifecycle.service.ts`, `security.service.ts`). The auth-session service **matches** the backend; the account-lifecycle and security services **mostly do not** (see §9).

---

## 4. Status per Sprint 8.4 Phase

| Phase | Status | Key evidence |
|---|---|---|
| 1. Pre-implementation audit | 🟢 | This report |
| 2. Logout session revocation | 🔴 | `auth.py:855` revokes tokens only |
| 3. Password reset revocation | 🟠 | `auth.py:986` tokens only, no sessions |
| 4. Change-password consolidation | 🔴 | `auth.py:1087` + `auth_lifecycle.py:197` + legacy `auth.py:1120` |
| 5. Temporary password system | 🔴 | `organizations.py:347` metadata_json vs `auth_enforcement.py:154/165` columns |
| 6. Force password change | 🟠 | enforcement dep exists; broken for invite users; flag not cleared in `auth.py:1087` |
| 7. Account reactivation | 🔴 | 3 divergent restore flows; `users.py:462` blocked by `enforce_all_auth_policies`; `auth_lifecycle.py:368` doesn't set `is_active=True` |
| 8. Account unlock unification | 🔴 | dual fields (`user.py:127–133` vs `:160–167`) |
| 9. Account export | 🔴 | `account_lifecycle_service.py:137–143` AttributeError |
| 10. Invitation authorization | 🔴 | `auth.py:1588/1654` no email binding; reject unauth |
| 11. Refresh token family | 🔴 | `auth.py:374–415` reuse not detected, family not revoked |
| 12. Permanent deletion | 🟠 | 2 purge impls (`celery_app.py:314` vs `tasks/account_cleanup.py:26`); 3 delete flows |
| 13. Rate limiting | 🔴 | never registered; stale paths |
| 14. Wire dead routers | 🔴 | `device_trust`, `mfa_recovery`, `audit_logs` unmounted |
| 15. MFA consolidation | 🟠 | impl A wired; impl B (table/service) dead + async/sync mismatch |
| 16. Session consolidation | 🟠 | `/auth/sessions` + `/sessions` duplicate |
| 17. Admin authorization | 🔴 | users CRUD + account-lifecycle IDOR |
| 18. Email system hardening | 🟠 | all functions exist; 6 dead; 2 broken URLs; param quirk |
| 19. Campaign email bug | 🔴 | `Contact.id` passed as `User.id` |
| 20. RBAC hardening | 🟠 | RoleChecker works; permission granularity/keys broken; `require_permission` unused |
| 21. Audit logging | 🟠 | `auth.py:126` correct; `auth_lifecycle.py:98` & `auth_session.py:86` broken; reads not role-gated |
| 22. Testing | 🟢 | 659 passed, 0 failed across full suite |
| 23. PostgreSQL verification | 🟢 | Postgres-only ✅, single migration head ✅, Base columns on all tables ✅, model/schema parity (0 missing columns) ✅ |
| 24. Docker verification | 🟢 | full stack healthy; register→login-gate→verify→authenticated request verified; worker tasks succeed |
| 25. Manual E2E | ⚫ | not run |

---

## 5. Duplicate / Competing Implementations (must reconcile)

| Concern | Implementations | Location |
|---|---|---|
| **Change password** | ① `/auth/change-password` ② `/auth/change-password` (same path, **collision** — first registered wins) ③ legacy `/auth/password-change` | `auth.py:1087`, `auth_lifecycle.py:197`, `auth.py:1120` |
| **Session management** | `/auth/sessions` vs `/sessions` | `auth_session.py`, `sessions.py` |
| **Audit** | `/audit` (mounted) vs `/security/audit` (dead) | `audit.py`, `audit_logs.py` |
| **Account deletion** | `DELETE /users/me` (immediate soft-delete) vs `POST /users/me/delete` (7-day) vs `POST /auth/account/delete` (7-day, doesn't deactivate) | `users.py:321/373`, `auth_lifecycle.py:301` |
| **Account restore** | `/auth/restore-account` (proxy) vs `/users/me/restore` vs `/auth/account/restore` (email+password) | `auth.py:792`, `users.py:458`, `auth_lifecycle.py:368` |
| **MFA recovery** | preference-JSONB codes (wired) vs `MFARecoveryCode` table + service (dead) | `auth.py:1211`, `mfa_recovery.py` |
| **Account purge** | Celery beat `purge_deleted_accounts_task` (hourly, soft) vs APScheduler `run_account_cleanup` (daily, full) | `celery_app.py:314`, `tasks/account_cleanup.py:26` |
| **Lockout fields** | login uses `locked_until`/`failed_login_count`; unlock uses `is_locked`/`failed_login_attempts` | `auth.py:418–456`, `account_lifecycle_service.py` |
| **Temp-password state** | metadata_json (`is_temporary_password`, `change_password_required`) vs explicit columns | `organizations.py:347`, `user.py:168–179` |

---

## 6. Verified Security Vulnerabilities

| # | Finding | Severity | Location |
|---|---|---|---|
| 1 | **List all users** — any authenticated user (incl. GUEST) gets every user's email/name/superuser/role | 🔴 Critical | `routes/users.py:77–93` |
| 2 | **Modify any user** — `setattr` of arbitrary fields incl. `is_superuser`, `email`, `password` on any UUID | 🔴 Critical | `routes/users.py:277–311` |
| 3 | **Hard-delete any user** — `db.delete(user)` with only `get_current_user` | 🔴 Critical | `routes/users.py:349–363` |
| 4 | **IDOR on account lifecycle** — `/{user_id}/unlock`, `/{user_id}/export`, `/{user_id}/status`, `/{user_id}/history` require no admin/ownership; unlock any account | 🔴 Critical | `routes/account_lifecycle.py:159,313,445,472` |
| 5 | **Reject invitation unauthenticated** — no auth dependency; anyone with token rejects it | 🔴 High | `routes/auth.py:1654` |
| 6 | **Accept invitation without email binding** — authenticated user can accept an invite meant for another email | 🔴 High | `routes/auth.py:1588–1651` |
| 7 | **Register-with-invitation without email binding** — new user with any email joins the invite's org | 🔴 High | `routes/auth.py:600–616,654–666` |
| 8 | **Invitation resend permissive** — explicit `# TODO`; any authenticated user can rotate/resend any org's invite | 🔴 High | `routes/auth_lifecycle.py:149–150` |
| 9 | **MEMBER can edit org AI security policies** | 🟠 High | `routes/security.py:147,176,198` |
| 10 | **No brute-force protection** — rate limiting never registered | 🔴 High | `main.py:40–48` |
| 11 | **Audit trail readable by any org member (incl. GUEST)** | 🟠 Medium | `routes/audit.py:71–144` (`_require_admin_or_superuser` is a no-op `:61`) |
| 12 | **`require_permission`/`PermissionChecker` never used** by any route | 🟠 Medium | `core/deps.py:187`, `middleware/rbac.py:130` |
| 13 | **Service-layer RBAC role-key mismatch** — membership roles (`OWNER/ADMIN/…`) don't match `DEFAULT_ROLE_PERMISSIONS` keys (`super_admin/…`) → checks only pass for superuser; `admin:users:export` never granted | 🟠 Medium | `services/base/permissions.py:92`, `services/base/authorization.py:33–44` |
| 14 | **MFA secret stored in plaintext** (model comment claims AES-256) | 🟠 Medium | `routes/auth.py:1173`, `user.py:122` |
| 15 | **Mock OAuth bypass** in dev/test env (any `mock_*` token creates a user) | 🟡 Low | `routes/auth.py:1481–1488` |
| 16 | **Public observability metrics/health** exposing infra state | 🟡 Low | `routes/observability.py:25–113` |

---

## 7. Verified Runtime Bugs / Guaranteed Failures

| # | Bug | Impact | Location |
|---|---|---|---|
| 1 | `UserSession` model uses `timezone` without import | `NameError`; session tests error out | `models/iam.py:28,334` |
| 2 | Route/`last_activity_at` vs model `last_active_at` | 500 on session listing | `routes/auth_session.py:113,127,140` |
| 3 | `from api.models.audit import AuditLog` — module doesn't exist (lives in `platform_events`) | `ModuleNotFoundError` | `services/audit_log_service.py:54,97,149,189,219` |
| 4 | `log_audit` builds `AuditLog(user_id=…, ip_address=…, user_agent=…, metadata=…)` — invalid kwargs | `TypeError` → 500 on resend-invite, change-password, account-delete/restore, session ops | `routes/auth_lifecycle.py:98–108`, `routes/auth_session.py:86–97` |
| 5 | GDPR export reads `user.display_name`, `user.role`, `user.organization_id` — don't exist | `AttributeError`; export always fails | `services/account_lifecycle_service.py:137–143` |
| 6 | Phase-4 migrations omit `Base` columns (`deleted_at` etc.) | `column "deleted_at" of relation "trusted_devices" does not exist` | `alembic/versions/d3e4f5g6h7i8_…py:74–159` |
| 7 | `MFARecoveryService.generate_recovery_codes` raises unless MFA already enabled | Feature can't be used by tests/UI as specced | `services/mfa_recovery_service.py:112` |
| 8 | `auth_lifecycle.py` account/restore never sets `is_active=True` | User remains unable to log in after restore | `routes/auth_lifecycle.py:416–420` |
| 9 | `auth.py` change-password never clears `change_password_required` | Forced-password-change loops forever | `routes/auth.py:1087–1115` |
| 10 | `/users/me/restore` includes `enforce_all_auth_policies`, which 403s inactive users | Deactivated users can't restore via this path | `routes/users.py:462` + `middleware/auth_enforcement.py:139` |
| 11 | Duplicate `/auth/change-password` path (2 routers) | Only first is reachable; second is shadowed | `auth.py:1087`, `auth_lifecycle.py:197` |

---

## 8. Missing Functionality

- **Logout-all / session-revoke coverage on access tokens** (Phase 2).
- **Session revocation on password change** (both change-password endpoints revoke nothing).
- **Refresh-token family compromise handling** (revoke family, sessions, audit, alert).
- **Rate limiting** — middleware + service exist but are dead and misconfigured.
- **Mounting** of `device_trust`, `mfa_recovery`, `audit_logs` routers (Phase 14).
- **Temp-password plumbing**: explicit columns never populated by invite flow; enforcement reads columns that stay null.
- **Frontend pages**: change-password, MFA, sessions, roles/permissions, security settings.
- **`/auth/accept-invitation` and `/auth/verify-email-change` frontend routes** (backend builds these URLs).
- **Deletion confirmation email** (`auth_lifecycle.py:359` `# TODO: Send confirmation email`).
- **Email-change frontend flow**.
- **Admin authorization** on `users.py` CRUD + account-lifecycle admin endpoints.

---

## 9. Frontend ↔ Backend Contract Mismatches (`apps/web/src/services/*`)

| Frontend call | Backend actual | Status |
|---|---|---|
| `POST /account/deactivate` | `/account/lifecycle/deactivate` | MISMATCH |
| `POST /account/deletion/request` | no such route | MISSING |
| `DELETE /account/deletion/cancel` | no such route | MISSING |
| `DELETE /account/deletion/immediate` | no such route | MISSING |
| `POST /account/export` | `/account/lifecycle/export` | MISMATCH |
| `GET /account/export/{id}` | `/account/lifecycle/data-export` | MISMATCH |
| `GET /account/privacy-dashboard` | `/account/lifecycle/privacy-dashboard` | MISMATCH |
| `GET /security/devices` | `/security/devices/trusted` | MISMATCH |
| device body `device_fingerprint`/`remember_for_days` | `device_name`/`duration_days` | MISMATCH |
| `POST /security/mfa/recovery-codes/generate` | `/security/mfa/recovery/generate` | MISMATCH |
| `POST /security/mfa/recovery-codes/verify` (expects `{valid, access_token}`) | `/security/mfa/recovery/verify` (`{success, …}`) | MISMATCH |
| `GET /audit/security-summary` | no such route | MISSING |
| `POST /auth/password-reset/request` | `/auth/forgot-password` | MISMATCH |
| `POST /auth/password-reset/verify` | no such route | MISSING |
| `POST /auth/password-reset/complete` | `/auth/reset-password` | MISMATCH |
| `GET/DELETE /auth/sessions*` | `/auth/sessions*` | ✅ MATCH |

(Device-trust and MFA-recovery routers are dead anyway — the backend has no reachable
endpoints to match.)

---

## 10. Email & Celery Findings

- **All 23 email functions exist** in `services/email_service.py` (Resend → SMTP → console fallback with retry, `EmailLog` write). ✅
- **6 dead templates** (defined, never called in production): `send_resend_verification_email`, `send_password_changed_email`, `send_new_login_email`, `send_new_device_email`, `send_mfa_enabled_email`, `send_mfa_disabled_email`. All security events instead go through generic `send_security_alert` (`auth.py:256,306,1105,1221,1265`).
- **Broken invitation URL:** `auth_lifecycle.py:164` builds `/auth/accept-invitation?token=…` — no such frontend page (404).
- **Broken email-change URL:** `users.py:222` builds `/auth/verify-email-change` — no such page.
- **`send_invitation_revoked_email`** called with the same email twice (`organizations.py:659`) — fragile, not an arg-swap today.
- **Two purge implementations run concurrently** and diverge in criteria/effects (see §5).
- **Campaign email (Phase 19):** `campaign_broadcast_task` (`celery_app.py:198–206`) passes `str(contact.id)` as `user_id_str` → `NotificationService` looks up a `User` by that id (`notification_service.py:71`) → never matches → **no email sent, silently**. The task also has zero callers / no beat entry.
- **Sensitive logging:** `core/redis_manager.py:81` logs the full `REDIS_URL` (may embed credentials). Dev-mode email fallback prints token-bearing URLs (`email_service.py:389–396,481–487`). No production logger prints raw passwords/tokens/secrets.

---

## 11. Test & Migration State

- **pytest:** 59 failed, 7 errors, 43 passed (~64 s). Clusters documented in `docs/sprint_8_3_1_diagnosis.md`: `timezone` import, session column name, dead audit import, migration Base columns, DDD-vs-`db=` service contract, restore/MFA feature gaps.
- **Migrations:** single linear chain, head `d3e4f5g6h7i8` (`alembic heads` OK). **Problem:** `trusted_devices`, `mfa_recovery_codes`, `rate_limit_log` created without `deleted_at`/`created_by`/`updated_by`/`version` that `Base` (`database/base.py:62–87`) requires. Phase 1–3 migrations should be checked for the same.
- **PostgreSQL-only** (no SQLite introduced). `eaimos_local`/`eaimos_test` DBs in use.

---

## 12. Acceptance-Criteria Assessment (Sprint 8.4)

| Criterion | State |
|---|---|
| Logout actually revokes active session | ❌ Not met (`auth.py:855`) |
| Password reset revokes previous sessions | ❌ Not met (`auth.py:986`) |
| One canonical change-password implementation | ❌ 2–3 implementations |
| Temp-password stored & enforced consistently | ❌ metadata_json vs columns |
| Temp-password users blocked from dashboard | ⚠️ enforcement exists but never fires for invite users |
| Deactivated users have safe restoration flow | ❌ fragmented + blocked path |
| Lock/unlock uses same fields | ❌ dual fields |
| Account export works without missing fields | ❌ crashes |
| Invitation authorization verifies identity/email | ❌ not verified |
| Refresh-token reuse revokes family | ❌ not implemented |
| Permanent deletion one canonical impl | ❌ two purge paths + three delete flows |
| Rate limiting registered & active | ❌ not registered |
| Required IAM routers mounted & tested | ❌ 3 routers unmounted |
| MFA one canonical impl | ⚠️ two impls (one wired) |
| Session mgmt one canonical impl | ⚠️ two routers |
| Admin endpoints enforce backend authorization | ❌ critical IDOR/vulns |
| RBAC enforced server-side | ⚠️ partial; granularity broken |
| Security events audited | ⚠️ 2 broken helpers; read not gated |
| Required emails sent | ⚠️ all exist, 6 unused, 2 broken URLs |
| Campaign email recipient mapping correct | ❌ Contact.id→User.id |
| Backend tests pass | ❌ 59 fail / 7 error |
| Frontend tsc / build pass | ⚠️ not verified |
| Migrations valid | ⚠️ head OK; tables missing Base columns |
| Docker services start | ⚫ not verified |
| E2E flows work in Docker | ⚫ not verified |

---

## 13. Remediation Roadmap (suggested order)

1. **Fix guaranteed runtime crashes** (§7): `timezone` import, session column name, audit import typo, broken `log_audit` helpers (2 files), migration Base columns (add-column migration), export AttributeError.
2. **Close critical authorization holes** (§6 #1–#5): add `get_current_admin_user`/org-role checks to `users.py` CRUD + `account_lifecycle.py` admin endpoints; bind invitations to identity (email match) and require auth for reject; remove the permissive resend TODO.
3. **Fix Phase 2/3 session semantics**: logout revokes the active `UserSession`; reset-password & change-password revoke all sessions; change-password clears `change_password_required`.
4. **Consolidate duplicates** (§5): canonical change-password (keep `auth_lifecycle.py:197` — it already supports temp-password + clears flags — and fix its audit call); canonical deletion/purge service; single restore path that sets `is_active=True`.
5. **Phase 5/6 temp-password**: populate explicit `User` columns on invite; align `auth_enforcement` and frontend reads to one representation.
6. **Phase 8 unlock**: pick one field set (`locked_until`/`failed_login_count`), unify login + unlock + admin unlock.
7. **Phase 11 refresh families**: implement reuse detection → revoke family + sessions + audit + alert.
8. **Phase 13 rate limiting**: register middleware, correct the path table, add 429 handling for login/register/forgot-password/reset/MFA.
9. **Phase 14 mounting**: mount `device_trust`/`mfa_recovery`/`audit_logs` only after making them consistent (sync DB, canonical signatures); otherwise remove them.
10. **Phase 19 campaign email**: resolve recipients via `Contact.email` directly, add regression test.
11. **Frontend/backend contract alignment** (§9) + missing pages.
12. **Testing, build, Docker, E2E** (Phases 22–25).

---

## 14. Appendix — Verified Reference Index

| Concern | File:line |
|---|---|
| Router mounting / dead routers | `main.py:11,40–48,51–88` |
| All-users leak | `routes/users.py:77–93` |
| Arbitrary user update | `routes/users.py:277–311` |
| Hard delete user | `routes/users.py:349–363` |
| Account-lifecycle IDOR | `routes/account_lifecycle.py:159,313,445,472` |
| Login / lockout / MFA gate | `routes/auth.py:719–789` |
| Logout (tokens only) | `routes/auth.py:855–868` |
| Reset-password (no session revoke) | `routes/auth.py:943–997` |
| Refresh rotation (no family logic) | `routes/auth.py:374–415` |
| Change-password (no flag clear) | `routes/auth.py:1087–1115` |
| Temp-password change (canonical) | `routes/auth_lifecycle.py:197–298` |
| Account delete / restore (lifecycle) | `routes/auth_lifecycle.py:301–434` |
| Invite accept / reject | `routes/auth.py:1588–1689` |
| Invite creation (metadata_json temp pw) | `routes/organizations.py:340–347` |
| Invitation resend (permissive + bad URL) | `routes/auth_lifecycle.py:115–194` |
| Enforcement deps (column-based) | `middleware/auth_enforcement.py:120–219` |
| Broken audit helpers | `routes/auth_lifecycle.py:98–108`, `routes/auth_session.py:86–97` |
| Session model timezone bug | `models/iam.py:28,334` |
| `last_active_at` vs `last_activity_at` | `models/iam.py:332` / `routes/auth_session.py:127` |
| Duplicate lockout fields | `models/user.py:127–133,160–167` |
| GDPR export crash | `services/account_lifecycle_service.py:137–143` |
| Cleanup task (verified correct) | `tasks/account_cleanup.py:26–149` |
| Celery purge (divergent) | `worker/celery_app.py:314–348,478–506` |
| Campaign email bug | `worker/celery_app.py:198–206`, `services/notification_service.py:71` |
| Rate-limit middleware (dead) | `main.py:40–48`, `middleware/rate_limiting.py:20–26` |
| MFA recovery dead duplicate | `routes/mfa_recovery.py`, `services/mfa_recovery_service.py` |
| Audit model fields | `models/platform_events.py:141–209` |
| RBAC permission-key mismatch | `services/base/permissions.py:92`, `services/base/authorization.py:33–44` |
| Migration Base-column gap | `alembic/versions/d3e4f5g6h7i8_…py:74–159` |
| Frontend contract mismatches | `apps/web/src/services/account-lifecycle.service.ts`, `security.service.ts`, `auth.service.ts` |
