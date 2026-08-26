# EAIMOS Core Platform + AI Gateway — Deep Audit
## 01 — Executive Summary

**Audit date:** 2026-08-19
**Audit type:** Read-only / evidence-based (no code changes)
**Scope:** Core Platform + AI Gateway only
**Target repo:** `D:\markai` — branch `ps-f` (HEAD `ee00347`, working tree dirty — 80+ modified/untracked files)
**Interpreter used:** `D:\markai\.venv\Scripts\python.exe` (Python 3.13.7, pytest 9.1.1, editable install of `api` → `D:\markai\apps\api`)

---

## 1. What is complete

- **Database model layer** for Core Platform and AI Gateway is broadly present: `User`, `Organization`, `UserOrganization` (membership), `Role`, `Permission`, `AuditLog`, `SystemConfiguration`, `APIKey`, sessions, `AIModelRegistry`, `AIProvider`/`AIProviderKey`, `AITokenUsage`, `AIRoutingPolicy`/`AIRoutingLog`, `AIOrgLimit`, `AgentMemory`, `DocumentChunk`/`DocumentChunkEmbedding` — 39 Alembic migrations (40 revision files) exist and the test harness migrates them cleanly (`alembic upgrade head` succeeds against PostgreSQL).
- **Repository layer** is architecturally strong: `BaseRepository` (full CRUD, soft-delete, optimistic locking, offset + keyset pagination), `TenantRepository` (org-scoped reads/writes), `UnitOfWork`, filter/sort builders. `tests/test_core_repositories.py` verifies tenant isolation + optimistic locking against a real DB.
- **Service layer** scaffolding is enterprise-grade on paper: `BaseService` lifecycle (permissions, hooks, UoW transactions, read/write-through caching, domain events, ServiceResult error mapping), `ServiceContext`, `ValidatorChain`, `AuthorizationService`, `EventDispatcher` with retry/DLQ, `@transactional`.
- **Auth surface**: JWT access/refresh with refresh-token family rotation + reuse detection, session revocation, MFA (TOTP), account lockout, password reset, email verification, RBAC assignment hardening (Phase 20), DB-backed rate limiting middleware — implemented and mostly tested.
- **AI Gateway orchestration**: `AIGateway` coordinator with provider-adapter lookup (user → org → env keys), retry with exponential backoff, model blacklisting on failure, failover logging, usage/cost recording, health tracking, and a real SSE streaming runtime.
- **Frontend** has real API clients for auth, orgs, users, CRM, campaigns, chat (incl. streaming), knowledge, prompts, AI playground/compare/health/usage/routing — wired to the backend.

## 2. What is partial

- **Migration/model parity**: drift-and-fix pattern; several open gaps (infrastructure tables missing `version` column; `Permission` column shape mismatch vs routes; `TrustedDevice`/`MFARecoveryCode`/`RateLimitLog` models not exported; MFA recovery codes stored in `user.preferences` JSON instead of the dedicated table).
- **Provider integration**: adapters exist for Groq, OpenAI, Gemini, Claude, OpenRouter, DeepSeek, Mistral, Ollama + image providers, but **none are runtime-verified**; embeddings are simulated for Groq; streaming token/cost accounting is approximate (word counts); several providers rely on hardcoded model names.
- **RAG**: the *route-level* pipeline is real (embed → hybrid search → MMR rerank → context → LLM) but the *service-layer* RAG/retrieval/embedder classes are stubs, and `VectorSearchService.search_vector_index` fabricates results.
- **Memory**: buffer is in-memory only (20 messages); persistent org/agent memory exists but no retention/expiry/security review.
- **Frontend**: many dashboards/pages mix real API calls with hardcoded/mock chart data, simulated streaming animations, and local-state-only forms (AI settings API keys, admin audits).
- **Testing**: real PostgreSQL integration tests exist and mostly pass (650 pass once boot is fixed), but the suite is currently **un-runnable** in the working tree (see §4) and AI provider calls are all mocked.

## 3. What is missing

- **A booting, deployable API**: the application currently does not import (see §4). This is the single biggest gap.
- **Real provider connectivity verification**: no test or health check exercises a live provider; credentials are mocked in tests and the env keys were not runtime-tested (they are empty in test env).
- **Real vector search**: the only non-fabricated vector path is in `services/vector_store.py` + `services/rag_engine.py`; the structured service layer fabricates results.
- **Real AGUI execution**: `AGUIExecutionService.execute` returns a mock payload with a hardcoded `gpt-4o` model and a fake Card schema.
- **Security hardening**: security headers, resource limits in compose, secret rotation, encrypted integration credentials, org-scoped provider-key access, admin-gated provider-key writes, path-traversal-safe file handling.
- **Observability-to-frontend wiring** for AI usage/cost: usage dashboards seed synthetic data (`seed_dummy_usages`).

## 4. What is broken (P0/P1)

1. **P0 — The API cannot boot.** `apps/api/src/api/routes/account_lifecycle.py:261` uses `Depends(get_user_org_membership)` and `UserOrganization` which are **not imported** → `NameError` at import time; `main.py` imports this router so the whole app fails to start. The committed HEAD baseline is *also* broken (`apps/api/src/api/routes/users.py:103` SyntaxError: parameter without a default follows one with a default). Consequences: `uvicorn`/`docker compose up api` fails, and the **entire pytest suite errors at collection** (conftest imports `api.main`).
2. **P0 — Production secrets committed to git.** `.env.production` and `.env.test` are tracked; contain the real JWT `SECRET_KEY`, DB credentials, MinIO credentials, and AI provider keys. The Fernet encryption master key is derived from `SECRET_KEY` (`core/encryption.py:11`), so all "encrypted" provider keys are decryptable by anyone with repo access. JWT is HS256 with that key (`core/security.py:10,70,92`) → **token forgery**.
3. **P1 — Cross-tenant audit-log read.** `routes/audit.py` list + stats endpoints accept a client-supplied `organization_id` and filter on it without verifying membership (`audit.py:96-121,184-193`); the admin-guard helper is a no-op (`_require_admin_or_superuser`, `audit.py:61-66`).
4. **P1 — Open org registration.** `POST /auth/register` accepts `organization_id` and joins the caller as MEMBER with no invitation check (`auth.py:746-757`).
5. **P1 — OAuth account takeover.** `auth.py:1515` logs into an existing user whose email matches the OAuth provider without verifying an existing OAuth link; `mock_*` tokens accepted outside production.
6. **P1 — Production code returns fabricated AI data.** `VectorSearchService.search_vector_index` returns random UUIDs + canned snippets (`vector_search_service.py:40-52`); `AGUIExecutionService.execute` returns a mock payload (`agui_execution_service.py:66-76`); `routes/ai.py:1092-1147` seeds 120 synthetic usage rows into the live DB.
7. **Test suite: 9 failures** (measured on a boot-fixed copy): account-lifecycle reactivation/data-export tests (401) and an email-infrastructure alert test. See `07_TESTING_VALIDATION_AUDIT.md`.

## 5. Security vulnerabilities (headline)

| ID | Sev | Summary | Location |
|----|-----|---------|----------|
| SEC-01 | CRITICAL | Committed production secrets + JWT forgery + defeated encryption | `.env.production`, `.env.test`; `core/security.py:10,70,92`; `core/encryption.py:11` |
| SEC-02 | HIGH | Path traversal (Windows) — arbitrary file write/read via unsanitized extension | `routes/knowledge.py:487-493`, `1509-1520` |
| SEC-03 | HIGH | Plaintext / unencrypted provider API keys | `routes/ai.py:1582-1596`; `models/integration.py` (IntegrationCredential) |
| SEC-04 | HIGH | Cross-tenant audit-log read | `routes/audit.py:96-121,184-193` |
| SEC-05 | HIGH | Open org registration (no invite) | `routes/auth.py:746-757` |
| SEC-06 | HIGH | OAuth account takeover + dev `mock_` bypass | `routes/auth.py:1515,1609-1617` |
| SEC-07 | HIGH | Hardcoded default admin seeded + printed | `main.py:170-201` |
| SEC-08 | MEDIUM | User-level provider key lookup ignores org | `ai/gateway/coordinator.py:62-71` |
| SEC-09 | MEDIUM | Any active member can rotate org provider keys | `routes/ai.py` provider update endpoints |
| SEC-10 | MEDIUM | Global handler leaks `str(exc)`; no security headers | `main.py:224-239` |
| SEC-11 | MEDIUM | Frontend JWT in localStorage; refresh token in URL query | `apps/web/src/services/api-client.ts:22,60` |
| SEC-12 | MEDIUM | Login rate-limit keyed on username not IP; org enumeration | `routes/auth.py:820-834` |

Full details: `04_SECURITY_VULNERABILITY_AUDIT.md`.

## 6. Performance risks

- 100+ direct `db.query` calls in routers (`ai.py` 51, `knowledge.py` 65, `organizations.py` 42, `auth.py` 44, `chat.py` 32, …) bypassing repository caching/tenant logic.
- N+1 query patterns (e.g. per-member user fetch in `organizations.py:106-125`; per-role permission load in `rbac.py`).
- **Synchronous SQLAlchemy session used inside async services** — blocks the event loop (`services/base/unit_of_work_service.py` imports sync `SessionLocal`); async engine in `core/database.py` is unused by the request path.
- `get_current_user` performs a DB **write + commit on every authenticated request** (`core/deps.py:74-76`).
- Large-`OFFSET` pagination everywhere (`skip`/`limit`); keyset cursor exists in repositories but routes rarely use it.
- No connection-pool tuning, no resource limits in `docker-compose.yml`, unbounded upload dir with 100+ orphan files.
- AI: retry storms possible (3 retries × exponential backoff per provider in chain), cache stampedes on health checks, synchronous provider calls in request path, hardcoded per-call cost double-counting risk.

Details: `05_PERFORMANCE_SCALABILITY_AUDIT.md`.

## 7. Scalability risks

- Targets (100k users / 20k concurrent / <180 ms API / 99.9%) are **DESIGNED-FOR, never MEASURED**. No load tests, no benchmark artifacts, no latency measurements exist in the repo.
- Blocking sync DB session under async FastAPI caps throughput.
- Per-request DB writes (last_active_at) will not survive 20k concurrent.
- No pagination on many list endpoints beyond offset/limit; unbounded list scans.
- Event/cache layers exist but are not distributed-safe (in-memory idempotency set).

## 8. Static / hardcoded implementations

- Provider set, adapter map, env-key map, default adapter = Groq (`ai/gateway/coordinator.py:33-42,103-128`).
- Default models & pricing: `services/ai/constants.py`, `ai/cost/cost_tracker.py`, `ai/registry/manager.py` seed rows.
- Hardcoded model catalog: `routes/ai.py:77-86`; provider defaults in each adapter file.
- Hardcoded costs: image `cost_usd=0.04` (`ai/agents/image/executor.py:184`), vision/json token counts, prompt eval `0.0003`.
- Org-limit defaults `100.00 / 60 rpm / 50k tpm` (`coordinator.py:507-510`).
- Frontend: `API_KEYS_CONFIG`, `MODEL_PRESETS`, `TEMPLATES`, `MOCK_AUDITS`, chart data arrays.

**Intentional configuration vs unwanted hardcoding** is classified per-item in `08_STATIC_DYNAMIC_MOCK_AUDIT.md`.

## 9. Mock / simulation implementations

Production-path fabrications: `VectorSearchService.search_vector_index` (random results), `AGUIExecutionService.execute` (mock payload), `routes/ai.py seed_dummy_usages` (120 synthetic rows), Groq `embeddings` (MD5 hash vector), hardcoded `cost_usd=0.04`, prompt eval fake scores, `/ai/router/simulate`, dev-only sample fallbacks (gated on `ENVIRONMENT != "production"`). Frontend: simulated streaming/typing, mock charts, local-state-only AI key settings. Full inventory in `08_STATIC_DYNAMIC_MOCK_AUDIT.md`.

## 10. API integration gaps

- API contract drift: `Permission` serialization expects `resource`/`action`/`scope` columns that don't exist in the migration → silent failure.
- `update_organization` takes `name` as a **query parameter** instead of a body field (`organizations.py:138-158`).
- `/ai/providers/{name}/models` returns a hardcoded catalog that ignores the real registry.
- Audit-list tenant filter trusts client-supplied org id.
- No OpenAPI-documented rate-limit/error contract across providers; inconsistent error envelope between routers and the global handler.

## 11. Frontend integration gaps

- No `middleware.ts` → client-side-only route guarding; token in localStorage (XSS exposure).
- AI settings "API Keys" form is local-state only — saving just shows a toast (`features/ai-platform/pages/settings.tsx:79-86`).
- Usage/analytics dashboards mix seeded synthetic data with real endpoints.
- Dashboard home chart data mocked; several pages have `TODO`/disabled actions.
- API base URL falls back to `http://localhost:8000` because no `NEXT_PUBLIC_API_URL` is set in the web app.

## 12. Test failures (measured)

Ran the full suite on a **boot-fixed copy** of the working tree against PostgreSQL (eaimos-postgres container) with `-n 4`: **650 passed, 9 failed** (~4m10s). Failures: `sprint_8_3_1/test_account_lifecycle.py` (reactivate + 3 data-export tests) and `sprint_8_4/test_phase7_account_reactivation.py` (2) and `test_phase17_admin_authorization.py` (2) and `test_email_infrastructure.py` (1) — mostly 401s because the account-lifecycle endpoints now require an org-membership dependency the tests don't satisfy.

In the **actual working tree**, 100% of `apps/api/tests` errors at **collection** due to the boot-blocking NameError (conftest imports `api.main`). Domain scaffold tests pass: **14 passed**.

## 13. Test coverage gaps

- AI provider adapters: no live-provider tests (all mocked); no negative tests for 401/403/429/5xx per provider.
- No security tests for the vulnerabilities above (path traversal, org-registration, audit cross-tenant, token forgery).
- No performance/load tests; no benchmark harness.
- No frontend automated tests (no vitest/jest/playwright configured).
- `test_streaming.py` is fully mocked (unit-level only).
- Coverage tooling (`pytest-cov`) declared but not installed in the venv.

## 14. Production readiness

**NOT production-ready.** The API does not boot, secrets are compromised, encryption is defeated, tenant isolation has a confirmed bypass, and production code paths return fabricated AI data. It is a feature-rich prototype/alpha with a strong architectural skeleton.

## 15. Remaining work

Prioritized P0–P4 list with ~40 items in `09_REMAINING_WORK.md`.

## 16. Recommended execution order

1. **P0 — Restore boot**: fix `account_lifecycle.py` imports (and the HEAD `users.py` syntax error). Re-verify `docker compose up` and pytest collection.
2. **P0 — Rotate all secrets**, purge env files from git history, fix `.gitignore` (`*.env*`), separate Fernet key from `SECRET_KEY`.
3. **P0 — Fix cross-tenant audit read** + org-invite-only registration + OAuth link check.
4. **P1 — Remove production mock/fabricated paths** (vector search, AGUI, seed_dummy_usages, hardcoded costs).
5. **P1 — Harden file uploads** (extension whitelist, sanitized filenames, containment check).
6. **P2 — Real provider verification**, dynamic model catalog, encrypt-all-keys, admin-gated key writes.
7. **P2 — Migrate routes off direct ORM** onto repositories; fix sync/async session split.
8. **P3 — Performance**: indexes, pagination, query profiling, load testing, connection pooling.
9. **P4 — Frontend cleanup**: remove mock data, wire AI settings, add security headers, CSP, HTTP-only cookies.

---

## Scorecard

### Core Platform

| Dimension | Score | Basis |
|---|---|---|
| Architecture | 72/100 | Strong layered design; sync/async split and routing discipline undermine it |
| Database | 55/100 | Rich models + migrations, but drift, missing columns, missing exports, non-immutable audit |
| Repository | 68/100 | Excellent base; tenant bypass in inherited bulk/restore/hard-delete; cursor bug for string IDs |
| Service | 60/100 | Full lifecycle scaffolding; direct-ORM violations in 8+ service files; in-memory idempotency |
| REST API | 55/100 | Complete route coverage; 100+ direct `db.query`; contract drift; audit tenant bug |
| Frontend integration | 50/100 | Real clients exist; pervasive mock data; AI settings not wired; localStorage tokens |
| Testing | 45/100 | Strong integration fixtures; suite un-runnable in working tree; 9 failures; no security/load tests |
| Security | 30/100 | Committed secrets, JWT forgery, defeated encryption, path traversal, org-registration, audit bypass |
| Performance | 40/100 | N+1s, sync session in async path, per-request DB writes, offset pagination, no pool tuning |
| Production readiness | 20/100 | Does not boot; secrets compromised; mocks in prod paths |

### AI Gateway

| Dimension | Score | Basis |
|---|---|---|
| Architecture | 70/100 | Coordinator/router/registry/telemetry layering is sound |
| Provider integration | 45/100 | 8+ adapters, but all unverified; Groq embeddings fake; hardcoded models |
| Routing | 60/100 | Real retry/blacklist/failover; fallback partly hardcoded; health checks are key-string checks |
| Credential security | 30/100 | Encrypted-at-rest defeated by committed key; plaintext config keys; org-scope gap in user keys |
| RAG | 45/100 | Route path real; service layer fabricated; vector index = Python cosine over JSONB |
| Memory | 40/100 | In-memory buffer; persistent tiers exist but no retention/expiry/security review |
| Streaming | 60/100 | Real SSE runtime; token/cost accounting approximate (word counts); no disconnect stress tests |
| Usage/cost | 40/100 | Multiple recorders + double-charge risk; hardcoded costs; synthetic seeded data |
| Testing | 40/100 | Provider calls mocked; gateway tests real-DB; no live-provider or negative-path tests |
| Security | 35/100 | Key exposure paths, org-scope gap, no rate limits on provider endpoints, secrets compromised |
| Performance | 45/100 | Sync calls in request path, retry storms, no caching of registry, no load tests |
| Production readiness | 25/100 | Fabricated responses in prod paths; no live provider verified; secrets compromised |

---

**Methodology note:** Every finding was verified by direct file reads with line numbers, git inspection, or a test run. Findings that could not be verified are explicitly marked **NOT RUNTIME VERIFIED**. No source file in the audited repo was modified; the test run used an isolated copy with the minimal boot fix applied (documented in `07_TESTING_VALIDATION_AUDIT.md`).