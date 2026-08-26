# EAIMOS Testing & Validation Audit
## 07 — Testing / Validation Audit

---

## 7.1 Test infrastructure

- **Framework:** pytest 9.1.1 (installed venv) vs poetry.lock pin `^8.2.2`/8.4.2 — **version drift**. `pytest-cov` declared but **not installed**.
- **Config:** `apps/api/pyproject.toml` — `addopts = "--import-mode=importlib"`, `asyncio_mode = "auto"`.
- **Fixtures (`tests/conftest.py`, 500 ln):** REAL PostgreSQL (`eaimos_test` / `eaimos_test_gwN` per xdist worker), schema via `alembic upgrade head`, extensions `vector`, `uuid-ossp`, `pg_trgm`, `unaccent`. Autouse fixtures: patch Redis (MockRedisClient), patch MinIO, patch DuckDuckGo HTTP, eager Celery, and **`patch_ai_gateway_adapters` mocks `chat`/`stream`/`embeddings`/`vision`/`json_output`/`health` on all 5 providers** with deterministic fake responses. All AI provider calls are therefore mocked; test AI keys are empty strings.
- **Location:** tests live under `apps/api/tests/` (~70 files), `apps/api/tests/routes/`, `apps/api/tests/services/` (sprint1–sprint12), `tests/sprint_8_3_1/`, `tests/sprint_8_4/`, plus scaffold tests in `src/api/domain/*/tests/`.

---

## 7.2 Result — actual working tree

```
$ python -m pytest tests -q
ImportError while loading conftest 'D:\markai\apps\api\tests\conftest.py'
  File "D:\markai\apps\api\src\api\routes\account_lifecycle.py", line 261
    org_membership: UserOrganization = Depends(get_user_org_membership),
E   NameError: name 'get_user_org_membership' is not defined
```
**Result: 0 collected — 100% ERROR at collection** for the entire `apps/api/tests` suite (conftest imports `api.main`, which cannot boot). Same for `tests/services/`.

**Committed baseline (HEAD `ee00347`) also fails to collect:**
```
File ".../src/api/routes/users.py", line 103
  user_in: UserUpdate,
  ^^^^^^^^^^^^^^^^^^^
SyntaxError: parameter without a default follows parameter with a default
```

Independent suites that do not import `api.main`:
- `src/api/domain/.../tests/`: **14 passed** (scaffold tests, mostly `assert True`).

---

## 7.3 Result — boot-fixed copy (methodology note)

To measure test health of the **current working-tree code** without modifying the audited repo, a full copy was made to a temp directory and the **minimal boot fix applied in the copy only** (imported `get_user_org_membership` + `UserOrganization` in `routes/account_lifecycle.py`). This was the only change. PostgreSQL was the running `eaimos-postgres` container.

```
$ python -m pytest tests -n 4 -q --no-header
... 9 failed, 650 passed, 1218 warnings in 250.66s (4m10s)
```

### Failing tests (9)

| Test | Failure mode |
|---|---|
| `sprint_8_3_1/test_account_lifecycle.py::TestAccountDeactivation::test_reactivate_account_success` | 401 on `/api/v1/account/lifecycle/reactivate` |
| `sprint_8_3_1/test_account_lifecycle.py::TestDataExport::test_export_user_data_json` | 401 on `/api/v1/account/lifecycle/data-export` |
| `sprint_8_3_1/test_account_lifecycle.py::TestDataExport::test_export_user_data_csv` | 401 |
| `sprint_8_3_1/test_account_lifecycle.py::TestDataExport::test_export_includes_all_user_data` | 401 |
| `sprint_8_4/test_phase7_account_reactivation.py::TestDeactivationReactivate::test_reactivate_deactivated_account` | 401 |
| `sprint_8_4/test_phase7_account_reactivation.py::TestDeactivationReactivate::test_reactivated_user_can_login` | 401 |
| `sprint_8_4/test_phase17_admin_authorization.py::TestDeleteUser::test_regular_user_cannot_delete_others` | 401/403 path |
| `sprint_8_4/test_phase17_admin_authorization.py::TestDeleteUser::test_admin_can_delete_user` | 401/403 path |
| `test_email_infrastructure.py::TestNewSecurityAndOrgAlerts::test_login_alert_new_browser_device_ip_country` | expected alert assertion |

**Root cause hypothesis for the 401 cluster:** the account-lifecycle endpoints were recently changed to require `get_user_org_membership` + `UserOrganization` dependencies; the tests authenticate but do not establish the org-membership context the new dependency requires, and the endpoints are part of the same uncommitted change set. These are integration failures between new auth requirements and existing tests.

### Passing high-value suites (sampled)
- `test_ai_gateway.py`, `test_ai_gateway_phase2/3/4.py`, `test_ai_gateway_db.py`, `test_ai_gateway_limits.py` — PASSED (real DB + mocked providers).
- `test_core_repositories.py` — PASSED (tenant isolation, optimistic lock, pagination, UoW rollback).
- `test_auth.py`, `test_rbac.py`, `test_ai_security_phase1c.py` — PASSED.
- `test_streaming.py` — PASSED (fully mocked unit test).
- `test_ai_infrastructure.py` — PASSED (mocked Redis/Celery, real DB/API).

---

## 7.4 Coverage map (NOT COVERED / gaps)

| Area | Status |
|---|---|
| Live AI provider calls (Groq/OpenAI/Gemini/Claude/OpenRouter) | 🧪 NOT COVERED (all mocked) |
| Provider error paths: 401/403/404/408/409/429/500/502/503/504 per provider | 🧪 NOT COVERED |
| Security tests: path traversal, open org registration, OAuth takeover, JWT forgery, audit cross-tenant | 🧪 NOT COVERED |
| Tenant isolation under every path (user-key resolution, audit stats, provider health logs) | 🧪 NOT COVERED |
| Performance/load/soak tests (targets unmeasured) | 🧪 NOT COVERED |
| Streaming: disconnect, cancellation, partial output, usage correctness | 🧪 NOT COVERED (unit-mocked only) |
| Frontend automated tests | 🧪 NOT COVERED (none configured) |
| RAG data-leakage / permission-filter negative tests | 🧪 NOT COVERED |
| Double-charge verification (retry/fallback usage dedup) | 🧪 NOT COVERED |
| Coverage measurement (`pytest-cov`) | ⚠️ declared, not installed |

---

## 7.5 Other tooling
- `compileall` on working tree: **clean** (no syntax errors).
- `mypy`: configured with `ignore_errors = true` (effectively disabled).
- `flake8`/`black`: configured; not run in this audit.
- Frontend: `package.json` has `lint`/`build` scripts; **no test script**; `next.config.ts` is default.

---

## 7.6 Verdict
| Dimension | Verdict |
|---|---|
| Fixtures quality | 🟢 Real Postgres + alembic + mocked external deps — good isolation |
| Suite runnability | 🔴 BROKEN in working tree (boot-blocking NameError) and at HEAD (SyntaxError) |
| Pass rate (boot-fixed copy) | 🟡 650 passed / 9 failed (98.6%) |
| Coverage breadth | 🟡 Broad functional coverage; critical security/perf/live-provider gaps |
| Frontend tests | 🔴 None |

Key conclusion: a **passing unit suite is currently unattainable because the app cannot boot**; even boot-fixed, the suite validates mocked-provider behavior only and does not exercise real providers, security boundaries, or performance.