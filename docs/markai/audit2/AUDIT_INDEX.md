# EAIMOS Audit2 — Index

Deep, evidence-based audit of the **Core Platform** and **AI Gateway** of the EAIMOS / MarkAI codebase (`D:\markai`, branch `ps-f`). Read-only; no code changes.

**Audit date:** 2026-08-19
**Key result:** The API currently does not boot (uncommitted `NameError` in `routes/account_lifecycle.py:261`; committed HEAD has a `SyntaxError` in `routes/users.py:103`), production secrets are committed to git, and production code paths return fabricated AI data.

---

## Documents

| # | Document | Contents |
|---|---|---|
| 01 | [01_AUDIT_EXECUTIVE_SUMMARY.md](./01_AUDIT_EXECUTIVE_SUMMARY.md) | 16-point executive summary, headline findings, scorecards for Core Platform and AI Gateway |
| 02 | [02_CORE_PLATFORM_AUDIT.md](./02_CORE_PLATFORM_AUDIT.md) | Models, migrations, repositories, services, routes, frontend integration (evidence with file:line) |
| 03 | [03_AI_GATEWAY_AUDIT.md](./03_AI_GATEWAY_AUDIT.md) | Providers, registry, routing, prompt rendering, RAG, memory, usage/cost, streaming, AGUI, error handling |
| 04 | [04_SECURITY_VULNERABILITY_AUDIT.md](./04_SECURITY_VULNERABILITY_AUDIT.md) | SEC-01…SEC-23 with severity, location, evidence, impact, attack scenario, fix |
| 05 | [05_PERFORMANCE_SCALABILITY_AUDIT.md](./05_PERFORMANCE_SCALABILITY_AUDIT.md) | PERF-01…20, targets vs measured, architecture risks |
| 06 | [06_API_FRONTEND_INTEGRATION_AUDIT.md](./06_API_FRONTEND_INTEGRATION_AUDIT.md) | API client, Core Platform + AI Gateway consumers, FE/INT gaps |
| 07 | [07_TESTING_VALIDATION_AUDIT.md](./07_TESTING_VALIDATION_AUDIT.md) | Test infra, run results (650 pass / 9 fail on boot-fixed copy; collection blocked in working tree), coverage gaps |
| 08 | [08_STATIC_DYNAMIC_MOCK_AUDIT.md](./08_STATIC_DYNAMIC_MOCK_AUDIT.md) | Static vs dynamic classification; MOCK-01…12 backend + FE-M1…12 frontend fabrications |
| 09 | [09_REMAINING_WORK.md](./09_REMAINING_WORK.md) | P0–P4 prioritized remaining work with evidence links |
| 10 | [10_FINAL_AUDIT_MATRIX.md](./10_FINAL_AUDIT_MATRIX.md) | Completeness matrix (🟢/🟡/🔴/⚠️/🔒/⚡/🧪/🔌) with implementation levels |

---

## Headline findings (full detail in linked docs)

1. **P0 — API cannot boot.** `apps/api/src/api/routes/account_lifecycle.py:261` NameError (uncommitted); HEAD baseline `users.py:103` SyntaxError. Entire pytest suite errors at collection. (`01`, `04 SEC-02`, `07`)
2. **P0 — Secrets committed to git.** `.env.production`, `.env.test` tracked; HS256 JWT key + Fernet key derived from the same `SECRET_KEY` → token forgery + decryption of all provider keys. (`04 SEC-01`)
3. **P0 — Cross-tenant audit-log read.** `routes/audit.py` trusts client-supplied `organization_id`. (`04 SEC-04`)
4. **P0 — Open org registration & OAuth takeover.** `routes/auth.py:746-757,1515,1609-1617`. (`04 SEC-05/06`)
5. **P1 — Path traversal (Windows) in knowledge upload/preview.** (`04 SEC-03`)
6. **P1 — Production mock/fabricated data.** Vector search, AGUI execution, `seed_dummy_usages`, Groq fake embeddings, hardcoded costs. (`08`)
7. **Tests:** 650 passed / 9 failed on a boot-fixed copy; live providers, security, and performance untested. (`07`)

---

## Scorecards (see `01` for basis)

| Core Platform | Score | AI Gateway | Score |
|---|---|---|---|
| Architecture | 72 | Architecture | 70 |
| Database | 55 | Provider integration | 45 |
| Repository | 68 | Routing | 60 |
| Service | 60 | Credential security | 30 |
| REST API | 55 | RAG | 45 |
| Frontend integration | 50 | Memory | 40 |
| Testing | 45 | Streaming | 60 |
| Security | 30 | Usage/cost | 40 |
| Performance | 40 | Testing | 40 |
| Production readiness | 20 | Security | 35 |
| — | — | Performance | 45 |
| — | — | Production readiness | 25 |

---

## Verification notes
- All findings verified via direct reads with line numbers, `git` inspection, or a test run. Items that could not be verified are explicitly marked **NOT RUNTIME VERIFIED**.
- No source file in the audited repo was modified. The test run used an isolated copy with the minimal boot fix, documented in `07`.
- PostgreSQL used for tests: `eaimos-postgres` Docker container (started for this audit, `localhost:5432`).