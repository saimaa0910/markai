# EAIMOS Core Platform — Deep Audit
## 02 — Core Platform Audit

Scope: Organization, User, Membership, System Configuration, Audit Logging, Tenant Management, Core Authorization, Core Repositories, Core Services, Core DTOs/Validators/Policies/Events/Cache, Core REST APIs, Frontend integration.

All paths relative to `D:\markai\apps\api\` unless noted. Every finding includes evidence.

---

## 2.1 Component inventory

### Database models (`src/api/models/`)
| File | Models | Status |
|---|---|---|
| `organization.py` | `Organization`, `OrganizationSettings`, `OrganizationInvitation` | ✅ present |
| `membership.py` | `UserOrganization` (+`UserRole` enum), `OrganizationInvitation` | ✅ present |
| `user.py` | `User` | ✅ present |
| `iam.py` | `Role`, `Permission`, `role_permissions` junction, `UserRole`, `UserSession`, `PasswordResetToken`, `APIKey`, `OAuthProvider`, `OAuthAccount`, `SecurityPolicy` | ✅ present |
| `auth.py` | re-export shim over `iam.py`/`platform_events.py` | ⚠️ works but obscures ownership |
| `platform_events.py` | `PlatformEvent` (32-118), `AuditLog` (121-236) | ✅ present |
| `admin.py` | admin suite + `SystemConfiguration` | ✅ present |
| `security.py` | `TrustedDevice`, `MFARecoveryCode`, `RateLimitLog` + AI security models | ⚠️ first 3 not exported in `models/__init__.py` |
| `ai_platform.py`, `ai_registry.py`, `ai_usage.py`, `router.py`, `infrastructure.py`, `memory.py`, `observability.py`, `knowledge.py` | AI Gateway tables | ✅ present |

### Base model (`src/api/database/base.py:39-88`)
- UUID PK, `created_at`/`updated_at` (server `now()`), `created_by`/`updated_by` (nullable VARCHAR), `deleted_at` soft delete, `version` optimistic-lock column. All models inherit.

### Repositories (`src/api/repositories/`)
`base.py`, `tenant.py`, `organization_repository.py`, `user_repository.py`, `membership_repository.py`, `system_config_repository.py`, `audit_log_repository.py`, `audit.py`, `search.py`, `pagination.py`, `filters.py`, `sorting.py`, `query_builder.py`, `unit_of_work.py`, `interfaces.py`, `exceptions.py`, `iam_repository.py`, plus feature repos.

### Services (`src/api/services/`)
- `base/`: `base_service.py`, `service_context.py`, `service_result.py`, `authorization.py`, `permissions.py`, `validators.py`, `cache.py`, `event_dispatcher.py`, `unit_of_work_service.py`, `dependency_provider.py`, `interfaces.py`, `events.py`, `service_exceptions.py`.
- `core/`: `organization_service.py`, `user_service.py`, `membership_service.py`, `system_config_service.py`, `audit_log_service.py`, `dependencies.py`.

### Routes (`src/api/routes/`)
`organizations.py` (906 lines), `users.py` (702), `auth.py` (1828), `audit.py` (228), `audit_logs.py`, `rbac.py` (501), `auth_lifecycle.py`, `auth_session.py`, `sessions.py`, `mfa_recovery.py`, `device_trust.py`, `account_lifecycle.py` (367), `infrastructure.py`, `notifications.py`, plus feature routes. `main.py` (349) and `app/main.py` wire the app.

---

## 2.2 Core database audit

### What is solid
- Single `Base` with UUID PKs, timestamps, soft-delete and optimistic-lock `version` on every entity.
- 40 alembic revision files; the test harness runs `alembic upgrade head` cleanly against PostgreSQL.
- AI/security/observability tables were added in later revisions and patched by follow-ups (`ad0d735184ae`, `3f3d767ad88d`).

### Issues

| ID | Sev | Finding | Evidence |
|----|-----|---------|----------|
| DB-01 | HIGH | Infrastructure tables (`AIBackgroundJob` etc.) inherit `Base.version` (NOT NULL, server_default "1") but migrations `681f83cf20d0` / `ad0d735184ae` never add a `version` column → inserts on those models reference a non-existent column | `models/infrastructure.py:6-75` vs migrations |
| DB-02 | HIGH | `Permission` migration creates only `name`/`description`; routes expect `resource`/`action`/`scope` — the `hasattr(Permission, "resource")` guard makes the failure silent | migration `b2c3d4e5f6a1` vs `routes/rbac.py:96-104,260` |
| DB-03 | MEDIUM | `AuditLog`/`PlatformEvent` are documented as immutable/append-only but inherit `Base` → carry `updated_at`/`deleted_at`/`version` and can be updated/deleted | `models/platform_events.py` vs design docs |
| DB-04 | MEDIUM | `TrustedDevice`, `MFARecoveryCode`, `RateLimitLog` defined but not exported from `models/__init__.py` | `models/security.py:122-239` vs `models/__init__.py:111-179` |
| DB-05 | MEDIUM | MFA recovery codes written into `user.preferences["mfa_recovery_codes"]` JSON; the dedicated `mfa_recovery_codes` table is never used | `routes/auth.py:1344-1351,1451-1463` |
| DB-06 | LOW | `605e80810f09` uses a `SafeOperations` wrapper that silently skips `create_table` when a table exists and never reconciles missing indexes/constraints → masks drift | `alembic/versions/605e...py:24-110` |
| DB-07 | INFO | `models/auth.py` is an import shim (`from api.models.iam import ...`), obscuring true definitions | `models/auth.py` |

---

## 2.3 Core repository audit

### Strengths
- `BaseRepository`: CRUD, bulk ops, soft delete/restore, optimistic locking (`expected_version` checks at `base.py:390-397,450-457`), offset + keyset pagination (`234-318`), filters/sorting, IntegrityError → domain error mapping (`106-117`).
- `TenantRepository`: injects `organization_id = ctx` on every read; stamps org on create; validates ownership on update/soft-delete (`tenant.py:73-273`).

### Issues

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| REP-01 | HIGH | **Tenant bypass via inherited methods**: `restore`, `hard_delete`, `bulk_delete`, `update_many`, `bulk_upsert` are NOT overridden in `TenantRepository`; base implementations operate on raw ids/filters with no org filter → a tenant-scoped repo can restore/hard-delete/update rows of another tenant | `repositories/tenant.py` vs `base.py:467-578` |
| REP-02 | MEDIUM | Cursor pagination coerces `uuid.UUID(str(cursor_id))` unconditionally → `ValueError` for String-id models (e.g. `models/infrastructure.py:9` id=String(36)) | `base.py:279,286` |
| REP-03 | MEDIUM | `bulk_upsert` is a per-row select→update/insert loop — not atomic, N+1, no `ON CONFLICT` | `base.py:560-578` |
| REP-04 | MEDIUM | No default eager loading anywhere → lazy-load N+1s in serializers (rbac.py, users.py) | e.g. `rbac.py:92,192`; `users.py:45` |
| REP-05 | LOW | `unit_of_work.py:16` imports the **sync** `SessionLocal` while exposing async context methods → services run sync DB work inside the event loop | `repositories/unit_of_work.py:16` |

### Direct ORM access outside repositories (violations)
Services that bypass the repository layer: `services/alert_engine.py:79`, `services/conversation.py:85,101,173,189,239`, `services/document_processing.py:59,64,217`, `services/email_service.py:228`, `services/marketing_agent_service.py:34,42,58,93,101,117`, `services/workflow_engine.py:63`, `services/notification_service.py`, `services/infrastructure/feature_flag_service.py:30`.

Routers with direct `db.query` (count per file): `ai.py` 51, `knowledge.py` 65, `organizations.py` 42, `auth.py` 44, `chat.py` 32, `rbac.py` 19, `users.py` 17, `auth_lifecycle.py` 13, `crm.py` 12, `workflows.py` 10, `memory.py` 10, `integrations.py` 7, `infrastructure.py` 6, `agents.py` 6, `audit.py` 6, `audit_logs.py` 1, `router.py` 2. **These bypass repository caching and tenant-injection logic.**

---

## 2.4 Core service audit

### Strengths
- `BaseService` lifecycle: permission enforcement, before/after hooks, UoW transactions, read/write-through caching with invalidation, buffered domain events dispatched after commit, tenant filter auto-injection on `list`, `require_tenant_access` checks, ServiceResult error mapping.
- `AuthorizationService` + role/permission matrix; `ValidatorChain`; `EventDispatcher` with retry/DLQ; `@transactional`.

### Issues

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| SVC-01 | HIGH | Direct-ORM queries inside services (listed in §2.3) violate the "services use repositories" rule | see §2.3 |
| SVC-02 | MEDIUM | Idempotency tracking is an in-memory set (`base_service.py:91,175`) — lost on restart, not distributed-safe | `services/base/base_service.py` |
| SVC-03 | MEDIUM | `UserService.get_by_email` caches under `user:email:<addr>` but never invalidates on update → stale reads | `services/core/user_service.py` |
| SVC-04 | MEDIUM | Async service layer drives a **sync** `SessionLocal` via UoW → blocking I/O on the event loop | `repositories/unit_of_work.py:16` |
| SVC-05 | LOW | Core services (`organization/user/membership/system_config/audit_log`) present and functional; seat quota via `count_by_org` works | `services/core/*.py` |

---

## 2.5 Core API audit

### Endpoint inventory (representative)
| Method | Path | Auth | Tenant check | Service/ORM | Notes |
|---|---|---|---|---|---|
| POST | /auth/register | public | ⚠️ no (joins any org) | ORM direct | `auth.py:746-757` |
| POST | /auth/login | public | — | ORM direct | refresh family rotation 409-496 |
| POST | /auth/refresh | token | — | ORM direct | reuse detection |
| POST | /auth/forgot-password / reset-password | public | — | ORM direct | anti-enumeration `1115-1116` |
| POST | /auth/mfa/… | user | — | ORM direct | codes in preferences JSON |
| POST | /auth/oauth/{provider} | public | ⚠️ no link check | ORM direct | `1515`, mock bypass `1609-1617` |
| GET | /organizations | user | yes | ORM direct | lacks `enforce_all_auth_policies` (`65-80`) |
| POST | /organizations | user | — | OrganizationService | correct service usage `36-62` |
| PATCH | /organizations/{id} | Owner/Admin | yes | ORM direct | name passed as **query param** `138-158` |
| DELETE | /organizations/{id} | Owner/Admin | yes | ORM direct | soft-delete without audit entry `161-191` |
| GET | /organizations/{id}/members | user | yes | ORM direct | N+1 loop `106-125` |
| GET | /users/me, /users | user | partial | ORM direct | superuser sees all `94-107` |
| PATCH | /users/me | user | — | ORM direct | avatar doesn't persist upload `157` |
| GET/POST | /audit/logs, /audit/stats | user | ⚠️ client-supplied org id trusted | ORM direct | **cross-tenant read** `96-121,184-193`; guard is a no-op `61-66` |
| GET | /roles, /roles/{id}, /permissions | user (auth only) | ⚠️ none | ORM direct | any member enumerates all roles `171-263` |
| POST/PATCH/DELETE | /rbac roles/assignments | OWNER/Admin | yes | ORM direct | assignment hardening present `320-451` |

### Issues

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| API-01 | HIGH | Audit log list/stats trust client `organization_id` without membership verification | `routes/audit.py:96-121,184-193` |
| API-02 | HIGH | Register endpoint joins any org without invitation | `routes/auth.py:746-757` |
| API-03 | MEDIUM | RBAC read endpoints unscoped (any member can read any org's roles by id) | `routes/rbac.py:171-263` |
| API-04 | MEDIUM | Business logic + direct ORM in routers (100+ sites) | see §2.3 |
| API-05 | MEDIUM | `get_current_user` DB write + commit on every request | `core/deps.py:74-76` |
| API-06 | MEDIUM | Inconsistent error envelopes between routers and global handler; no OpenAPI error contract | `main.py:224-239` |
| API-07 | LOW | Duplicate invitation accept/reject in both auth.py and organizations.py | `organizations.py:451-553` |
| API-08 | INFO | No global rate limit on general endpoints (only auth paths in middleware) | `middleware/rate_limiting.py` |

---

## 2.6 Core frontend integration

Real API wiring exists for login/register/users/settings/crm/campaigns/files/conversations. Gaps:
- Token in `localStorage` (`apps/web/src/services/api-client.ts:22,60`); refresh token sent as URL query param.
- No `middleware.ts` → client-side-only route guards.
- `settings` page: API keys are hardcoded local state; avatar upload simulated; `hasPermission` uses `userProfile.permissions.includes` (client-side only).
- Dashboard home chart data mocked (`apps/web/src/app/dashboard/page.tsx:74-85`).
- No `.env*` in `apps/web` → `NEXT_PUBLIC_API_URL` unset → hardcoded `http://localhost:8000` fallback.

Detailed inventory: `06_API_FRONTEND_INTEGRATION_AUDIT.md`.

---

## 2.7 Verdict

| Sub-area | Status | Score basis |
|---|---|---|
| Models | 🟡 PARTIAL | Complete surface; drift, missing exports, non-immutable audit |
| Migrations | 🟡 PARTIAL | 40 revisions, clean upgrade, but masked drift + 2 open gaps |
| Repositories | 🟢/🟡 COMPLETE w/ gaps | Tenant bypass in bulk/restore/hard-delete; cursor bug |
| Services | 🟡 PARTIAL | Full scaffolding; direct ORM violations; sync/async split |
| REST API | 🟡 PARTIAL | Full coverage; routing discipline failures; audit tenant bug |
| Frontend | 🟡 PARTIAL | Real clients; pervasive mocks; token security gaps |