# EAIMOS Static / Dynamic / Mock Audit
## 08 — Static, Dynamic & Mock/Simulation Audit

Classification: for every static item → INTENTIONAL CONFIGURATION vs UNWANTED HARDCODING. For every mock/simulation → legit test code, development-only, or **production runtime behavior**.

---

## 8.1 AI Gateway — dynamic vs static

### Dynamic (real, data/config-driven)
| Item | Mechanism | Evidence |
|---|---|---|
| Model registry | DB `AIModelRegistry`, seeded at runtime, `is_healthy` toggled live | `ai/registry/manager.py`, `ai/router/engine.py` |
| Provider registry | DB `AIProvider` + `AIProviderKey`, base_url overridable | `models/ai_platform.py`, `coordinator.py:115,133-134` |
| Credential resolution | 3-tier user → org → env, DB keys encrypted (intent) | `coordinator.py:44-139` |
| Routing rules | DB `AIRoutingPolicy` (scope/conditions/strategy) | `models/router.py`, `services/ai/model_router_service.py` |
| Cache/blacklist | Redis TTL blacklists for models/providers | `services/cache_service.py`, `coordinator.py:775` |
| Quota/limits | DB `AIOrgLimit`/`AIQuotaUsage` counters | `models/ai_platform.py`, `coordinator.py:495-528` |
| Org security policies | per-org seed in `ai/security/pipeline.py:85-112` | pipeline |
| Image provider priority | `OrganizationSettings (ai, default_image_provider)` | `ai/agents/image/provider_router.py:53-69` |

### Static / hardcoded
| Item | Value | Classification |
|---|---|---|
| Provider set + adapter map | 8 instances in `coordinator.py:33-42`, map `103-112` | INTENTIONAL (fixed catalog) — but should be registry-driven |
| Unknown-provider fallback | **GroqProvider** (`coordinator.py:114`) | UNWANTED HARDCODING (silent mis-route) |
| Env-key map | `coordinator.py:117-126` | INTENTIONAL (env contract) |
| Default models | `services/ai/constants.py` `DEFAULT_MODEL_PER_PROVIDER` | INTENTIONAL fallback config |
| Model pricing | `ai/cost/cost_tracker.py`; `constants.py` `MODEL_PRICING_PER_1K`; registry seed prices in `ai/registry/manager.py` | INTENTIONAL config, but **multiple disagreeing tables** → UNWANTED |
| Provider default models | groq.py:86, deepseek.py:27, mistral.py:26, ollama.py:27, google_imagen.py:51, pollinations.py:48, claude.py:34 (`max_tokens=4096`) | INTENTIONAL per-provider defaults |
| Model catalog endpoint | `routes/ai.py:77-86` (6 hardcoded models) | UNWANTED HARDCODING — ignores DB registry |
| Org limit defaults | 100.00 / 60 rpm / 50k tpm (`coordinator.py:507-510`) | INTENTIONAL default policy |
| OpenRouter referer/title | `openrouter.py:31-32` | INTENTIONAL |
| Prompt eval scores | 0.95/0.92/0.94 (`services/prompt.py:946-966`) | UNWANTED (fabricated) |
| Default embed model | `text-embedding-3-small` 1536 dim | INTENTIONAL |

---

## 8.2 Mock / simulation inventory

### Legit test code (test-only)
- `tests/conftest.py` provider mocks, MockRedisClient, in-memory MinIO, eager Celery — correct test isolation.
- `test_streaming.py` — fully mocked unit test (acceptable but shallow).

### Development-only behavior (guarded, acceptable but must not leak)
- `routes/auth.py:1610-1617` — `mock_` OAuth tokens accepted when `ENVIRONMENT != "production"`. ⚠️ Single misconfigured deploy opens auth bypass → should be test-only.
- Sample gateway fallbacks in `coordinator.py:825-834` (chat) and `1103-1111` (stream) gated on `settings.ENVIRONMENT != "production"` (default `"development"`).

### 🔴 PRODUCTION RUNTIME BEHAVIOR — violations (production code returns fabricated data)
| ID | Location | What it fabricates |
|---|---|---|
| MOCK-01 | `services/knowledge/vector_search_service.py:40-52` | Vector search results: random `uuid4()` chunk/document ids, `score=0.92-(i*0.05)`, canned snippet text — no DB access |
| MOCK-02 | `services/ai/agui_execution_service.py:66-76` | AGUI response payload with hardcoded `gpt-4o`, fake Card UI schema, "Mock AGUI response" comment |
| MOCK-03 | `routes/ai.py:1092-1147` (`seed_dummy_usages`) | Inserts 120 synthetic `AITokenUsage` rows (invoked from usage list `:1156` and analytics `:2612`) |
| MOCK-04 | `routes/ai.py:77-86` | Hardcoded model catalog response |
| MOCK-05 | `ai/providers/groq.py:122-142` | Deterministic MD5-hash 1536-dim "embedding" — silently used for vector search |
| MOCK-06 | `services/prompt.py:789-814` | Fallback `"Sample execution response."`, provider `"google"`, 60/40 token split |
| MOCK-07 | `ai/agents/image/executor.py:184`, `routes/ai.py:2529,1524` | `cost_usd = 0.04` hardcoded |
| MOCK-08 | `services/knowledge/document_ingestion_service.py:36-82` | `ingest_document` returns `INDEXED` without persisting |
| MOCK-09 | `ai/rag/pipeline.py:16-24`, `ai/retrieval/retriever.py:16-17`, `ai/embeddings/embedder.py:16-24` | TODO stubs (empty/zero results) |
| MOCK-10 | `routes/observability.py:446` | Admin-only simulated alert (dev) |
| MOCK-11 | `routes/router.py:190-191` | `POST /ai/router/simulate` endpoint |
| MOCK-12 | `services/ai/rag_service.py:116-119` | Dummy similarity 0.85 "SQLite fallback" |

### Frontend mock/simulation (UI-level)
| ID | Location | What |
|---|---|---|
| FE-M1 | `apps/web/src/app/dashboard/ai/page.tsx:44-46,132-134,162-176,399` | Mock streaming animation / "Stream mock bubble" |
| FE-M2 | `features/ai-platform/pages/settings.tsx:19-48,79-86` | API keys local-state only; save toasts only |
| FE-M3 | `features/ai-platform/pages/admin.tsx:34-38,45` | `MOCK_AUDITS` hardcoded |
| FE-M4 | `features/ai-platform/pages/analytics.tsx:81-96` | static radar data + `Math.random()` heatmap |
| FE-M5 | `features/ai-platform/pages/health.tsx:132-137,179-183` | mock timeline pulses, mock success % |
| FE-M6 | `features/ai-platform/pages/observability.tsx:76,541-547,678-680` | simulated alert toast, mock spans, simulate outages |
| FE-M7 | `features/ai-platform/pages/playground.tsx:26-48` | hardcoded templates with sampleResponse |
| FE-M8 | `features/ai-platform/pages/compare.tsx:28-79,155` | hardcoded MODEL_PRESETS, quality scores |
| FE-M9 | `app/dashboard/page.tsx:74-85` | mock chart data on home |
| FE-M10 | knowledge/prompts pages | simulated progress/typing/step activation |
| FE-M11 | `dashboard/agents`, `workflows`, `integrations`, `agents/analytics`, templates/marketplace | hardcoded stats/charts/catalogs |
| FE-M12 | `features/knowledge/pages/dashboard.tsx:44-60`, embeddings/search pages | mockStorage chart, simulated progress |

### TODO / FIXME / placeholder inventory (sampled)
- `ai/moderation/moderator.py:23`, `ai/prompts/manager.py:26` (stubs)
- `tasks/tasks.py` (`execute_background_job` returns `{"status": "completed"}` with TODO)
- `services/ai/memory_service.py:192-193` (`unittest.mock` usage in service)
- `services/ai/mappers.py:13,19,37`, `services/knowledge/mappers.py:13` (MagicMock fallbacks)
- Frontend: various `TODO`/disabled actions per `06` doc.

---

## 8.3 Verdict

- Static configuration is **mostly intentional** (env contracts, per-provider defaults, default policies) — the exceptions are the hardcoded model catalog endpoint, Groq-as-unknown-provider fallback, and the inconsistent pricing tables.
- Production **mock/simulated data is a systemic issue** (12 backend + 12 frontend locations). Any of MOCK-01/02/03/05/06 in a live deployment silently corrupts user-visible output, dashboards, and accounting.
- The guidance "production code must NOT silently return fake AI responses" is **violated**.