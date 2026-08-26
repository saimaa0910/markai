# EAIMOS Performance & Scalability Audit
## 05 — Performance / Scalability Audit

Targets: 100k registered users, 20k concurrent, API <180 ms, internal <45 ms, AI <2 s, 99.9% availability. **These targets are DESIGNED-FOR, not MEASURED** — no load tests, benchmarks, or latency artifacts exist in the repo.

---

## 5.1 Query-level findings

| ID | Sev | Finding | Evidence |
|----|-----|---------|----------|
| PERF-01 | HIGH | **Synchronous DB session in async request path.** Routers use sync `get_db` (`database/session.py`); services/`UnitOfWork` also drive the sync `SessionLocal` while exposing async APIs → the event loop blocks on every DB operation. Async engine (`core/database.py`) is unused by the request path. | `repositories/unit_of_work.py:16`, `core/database.py`, `database/session.py` |
| PERF-02 | HIGH | **DB write + commit on every authenticated request.** `get_current_user` updates `last_active_at` and commits. | `core/deps.py:74-76` |
| PERF-03 | HIGH | **100+ direct `db.query` calls in routers** bypass repository caching, tenant-injection, and eager-loading logic. Worst: `ai.py` 51, `knowledge.py` 65, `organizations.py` 42, `auth.py` 44, `chat.py` 32. | see §2.3 of `02_CORE_PLATFORM_AUDIT.md` |
| PERF-04 | HIGH | **N+1 query patterns.** Per-member `User` fetch in `organizations.py:106-125`; per-role `permissions` lazy load in `rbac.py:92,192`; per-user role load in `users.py:45`. | files cited |
| PERF-05 | MEDIUM | **Large-OFFSET pagination** on most list endpoints (`skip`/`limit`); keyset cursor exists in `BaseRepository` but is rarely used by routes. | `repositories/base.py:234-318` |
| PERF-06 | MEDIUM | **No default eager loading** anywhere; serializers trigger lazy loads. | e.g. `users.py`, `rbac.py` |
| PERF-07 | MEDIUM | **Vector search is Python-side**: cosine similarity over JSONB embeddings loaded into memory; no pgvector index (`<->` operator). | `services/vector_store.py`, `models/knowledge.py` |
| PERF-08 | MEDIUM | `bulk_upsert` per-row select→update/insert loop (no `ON CONFLICT`) | `repositories/base.py:560-578` |
| PERF-09 | LOW | `AuditLog` list filters use `ilike(f"%{action}%")` → full scan | `routes/audit.py:127` |

---

## 5.2 AI Gateway findings

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| PERF-10 | HIGH | **Synchronous provider calls in request path** (httpx sync clients, 30 s timeouts) — a slow provider blocks a worker thread entirely; no async httpx in providers. | `ai/providers/*.py` |
| PERF-11 | MEDIUM | **Retry storms**: up to 3 retries × exp backoff per provider; coordinator can retry multiple providers in a fallback chain with no global circuit breaker or rate budget. | `ai/gateway/coordinator.py:666-772` |
| PERF-12 | MEDIUM | **Cache stampede**: provider health checks scheduled per-minute and queried synchronously; no single-flight/mutex. | `worker/celery_app.py` beat schedule |
| PERF-13 | MEDIUM | Registry health status toggled in DB per failure; repeated DB writes during failover. | `coordinator.py:775-777` |
| PERF-14 | LOW | Per-request `decrypt_key` + provider re-instantiation in `_get_provider_adapter` (no memoization). | `coordinator.py:44-139` |
| PERF-15 | INFO | `ip-api.com` HTTP call on every login adds external latency. | `routes/auth.py:249` |

---

## 5.3 Concurrency & resources

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| PERF-16 | MEDIUM | **No connection-pool tuning** for the sync session factory; default pool sizes. | `database/session.py` |
| PERF-17 | MEDIUM | **No resource limits** (mem/cpu) in `docker-compose.yml` for any service — OOM-prone stack (observed: `eaimos-api` exited 137). | `docker-compose.yml`; `docker ps -a` |
| PERF-18 | MEDIUM | **In-memory idempotency set** in `BaseService` — lost on restart, not distributed. | `services/base/base_service.py:91,175` |
| PERF-19 | LOW | Unbounded upload dir: 100+ orphan `.txt` files in `src/api/uploads/` with no cleanup job for orphaned local files. | `uploads/*.txt` |
| PERF-20 | INFO | Celery: 16 tasks + 7-entry beat schedule; eager mode in tests. No concurrency/prefork tuning observed. | `worker/celery_app.py` |

---

## 5.4 Architecture-level risks for the targets

- **20k concurrent users** with a sync-session-per-request model and per-request DB write: the DB write amplification alone (20k writes/min+) requires connection pooling + batching; currently **not designed for it**.
- **<180 ms API latency**: no measurement exists; N+1 + sync session + external IP lookup per login make the target unlikely without rework.
- **99.9% availability**: single-node docker-compose, no HA, no auto-scaling config, no backup/restore evidence.
- **<45 ms internal latency**: no metrics collector to validate.

## 5.5 What is done well
- Repository keyset pagination exists (needs adoption).
- Redis cache layer with TTL + model/provider blacklisting prevents repeated failed calls.
- Background task framework (Celery) exists for heavy work (document pipeline, usage aggregation).
- OpenTelemetry + Prometheus + Grafana configured in compose (observability scaffolding present, but dashboards/alerts not verified).

## 5.6 Verdict
**Not measured, not production-tuned.** The architecture is directionally correct (layered, cached, evented) but the sync/async split, direct-ORM volume, N+1s, and absence of load testing keep it well below the stated targets until addressed.