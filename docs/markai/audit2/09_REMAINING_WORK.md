# EAIMOS Remaining Work — Prioritized
## 09 — Remaining Work

Priorities: **P0** critical security/data-loss/runtime, **P1** major broken feature/security, **P2** missing production functionality, **P3** performance/scalability, **P4** UX/docs/cleanup. **None of these were implemented during the audit.**

---

## P0 — Critical (security / data-loss / runtime)

| # | Item | Evidence |
|---|---|---|
| P0-1 | **Restore API boot.** Add `get_user_org_membership` + `UserOrganization` imports to `routes/account_lifecycle.py`; fix HEAD baseline `users.py:103` defaulted-parameter order. Verify `docker compose up api`, `/health`, and pytest collection. | `account_lifecycle.py:261`; `users.py:103` |
| P0-2 | **Rotate every secret** (SECRET_KEY, Groq/OpenAI/Anthropic/Gemini/OpenRouter keys, Postgres/MinIO creds). Purge `.env.production`/`.env.test`/`.env.sprint831` from git and history (BFG/filter-repo); update `.gitignore` to `*.env*` (allow `.env.example`). | git ls-files; `core/config.py:77-79` |
| P0-3 | **Split encryption key from SECRET_KEY.** Dedicated Fernet master key; re-encrypt stored provider keys. | `core/encryption.py:11` |
| P0-4 | **Fix cross-tenant audit-log read** — never trust client-supplied `organization_id`; derive org from caller membership; enforce admin/owner for audit access; fix the no-op guard. | `routes/audit.py:61-66,96-121,184-193` |
| P0-5 | **Invite-only org registration** — remove `organization_id`/`role` acceptance from public register; require pending invitation. | `routes/auth.py:746-757` |
| P0-6 | **OAuth account-takeover fix** — verify existing `OAuthAccount` link before login; remove `mock_` token acceptance from non-test code. | `routes/auth.py:1515,1609-1617` |
| P0-7 | **Path traversal hardening** in uploads/preview — extension whitelist, uuid-only filenames, `realpath` containment, never use stored ext for reads. | `routes/knowledge.py:487-493,1509-1520` |

---

## P1 — Major broken feature / security

| # | Item | Evidence |
|---|---|---|
| P1-1 | Remove/disable production fabricated paths: `VectorSearchService.search_vector_index`, `AGUIExecutionService.execute` mock, `seed_dummy_usages`, prompt "Sample execution response", hardcoded `cost_usd=0.04`, groq fake embeddings (wire real embedder). | `08_STATIC_DYNAMIC_MOCK_AUDIT.md` |
| P1-2 | Encrypt ALL provider keys (drop `sk-` exception) and rotate path; encrypt `IntegrationCredential` columns. | `routes/ai.py:1582-1596`; `models/integration.py` |
| P1-3 | Org-scope user-level provider-key lookup; admin/OWNER gate on provider-key writes; org-scope health-log queries. | `coordinator.py:62-71`; `routes/ai.py:1866+`; `:1959-1964` |
| P1-4 | Fix 9 failing tests + account-lifecycle auth contract (endpoints require org-membership; align tests or dependency). | `07_TESTING_VALIDATION_AUDIT.md` |
| P1-5 | Replace default admin seed with env-driven password; stop printing credentials. | `main.py:170-201` |
| P1-6 | Fix tenant isolation in inherited repository methods (`restore`/`hard_delete`/`bulk_*`/`update_many`) for `TenantRepository`. | `repositories/base.py:467-578` |
| P1-7 | Resolve migration/model drift: add `version` to infrastructure tables; align `Permission` columns (`resource/action/scope`) or routes; export `TrustedDevice`/`MFARecoveryCode`/`RateLimitLog`; move MFA recovery codes to dedicated table. | DB-01..DB-05 |
| P1-8 | Route-scope RBAC reads (roles/permissions/roles-by-id) to caller org. | `routes/rbac.py:171-263` |
| P1-9 | Global handler: stop returning `str(exc)`; add security headers + env-tightened CORS. | `main.py:224-239`; `main.py:28-38` |

---

## P2 — Missing production functionality

| # | Item |
|---|---|
| P2-1 | Real provider connectivity verification + automated smoke tests with test-keys; live model discovery via provider APIs instead of hardcoded catalog. |
| P2-2 | Replace fabricated vector search with pgvector index + real embeddings (single embedding model consistent with registry). |
| P2-3 | Real AGUI execution (render → model call → UI schema) replacing mock payload. |
| P2-4 | Usage/cost idempotency (request-level dedup key) to eliminate double-charge on retry/fallback; align pricing tables; accurate streaming token accounting from provider usage payloads. |
| P2-5 | Memory: retention/expiry policy, max-size enforcement, PII handling on write. |
| P2-6 | Frontend AI settings persistence (wire provider-key endpoints to the settings form); remove mock charts/dashboards from production UI. |
| P2-7 | Provider rate limiting + circuit breaker per provider; honor `Retry-After` on 429. |
| P2-8 | Replace direct `db.query` in routes/services with repository calls (esp. ai.py, knowledge.py, organizations.py, auth.py, chat.py). |
| P2-9 | Async DB engine/session for async services; remove sync-session-in-async path. |
| P2-10 | Fix `PATCH /organizations/{id}` body contract; fix `/ai/providers/{name}/models` to read DB registry. |
| P2-11 | Frontend auth hardening: httpOnly cookies, `middleware.ts` route guards, refresh token in body not URL. |
| P2-12 | API rate limiting on general endpoints (not just auth). |

---

## P3 — Performance / scalability

| # | Item |
|---|---|
| P3-1 | Eliminate per-request DB write/commit in `get_current_user` (throttled/batched last_active_at). |
| P3-2 | Add indexes for hot paths (audit logs by org+created_at, token usage by org+created_at, membership by user_id); kill `ilike('%...%')` scans. |
| P3-3 | Adopt keyset/cursor pagination in list routes. |
| P3-4 | Add eager loading (`selectinload`/`joinedload`) in serializers; eliminate N+1s. |
| P3-5 | Async httpx clients for providers; async embeddings; avoid per-request decrypt/re-instantiation. |
| P3-6 | pgvector index + chunk-level retrieval limits; document cleanup job for orphaned uploads. |
| P3-7 | Connection pool tuning; resource limits + health-based auto-restart in compose; HA/backup plan for 99.9%. |
| P3-8 | Load/soak benchmark harness against the 100k/20k/<180ms targets. |

---

## P4 — UX / documentation / cleanup

| # | Item |
|---|---|
| P4-1 | Remove TODO/FIXME and dead stub modules (`ai/rag/pipeline.py`, `ai/retrieval/retriever.py`, `ai/embeddings/embedder.py`, `ai/moderation/moderator.py`, `ai/prompts/manager.py`, `tasks/tasks.py`). |
| P4-2 | Frontend: purge mock chart/typing/streaming simulations from production pages; keep marketing simulators separate. |
| P4-3 | Consistent error envelope + OpenAPI error/rate-limit documentation. |
| P4-4 | `pytest-cov` install + coverage gate; add frontend test tooling. |
| P4-5 | Docs: reconcile `docs/` with reality (many docs claim completed features that are mocked). |
| P4-6 | Fix tooling drift (poetry.lock pytest 8.4.2 vs installed 9.1.1; mypy effectively disabled). |

---

## Recommended execution order
P0-1 → P0-2 → P0-3 → P0-4 → P0-5/6/7 → P1-1 → P1-2/3 → P1-4 → P1-5..9 → P2 → P3 → P4.