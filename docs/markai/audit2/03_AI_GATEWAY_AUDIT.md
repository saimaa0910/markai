# EAIMOS AI Gateway — Deep Audit
## 03 — AI Gateway Audit

Scope: provider registry, model registry, provider adapters, API-key resolution, routing, fallback, prompt rendering, variable rendering, RAG, memory, AI usage, token accounting, cost, streaming, AGUI, health, retries, timeouts, error handling, caching, rate limits.

All paths relative to `D:\markai\apps\api\src\api\` unless noted.

---

## 3.1 Provider audit

### LLM chat providers (`ai/providers/`)
| Provider | File | Env var | Streaming | Retry | Timeout | Hardcoded defaults | Key resolution |
|---|---|---|---|---|---|---|---|
| OpenAI | `openai.py` | `OPENAI_API_KEY` | yes | no (coordinator-level) | 30s | base `api.openai.com/v1` | env / DB (coordinator) |
| Groq | `groq.py` | `GROQ_API_KEY` (82) | yes | no | — | model gate `llama\|mixtral\|gemma\|qwen` else `llama-3.3-70b-versatile` (86); vision default `llama-3.2-11b-vision-instruct` (145); **embeddings = MD5-hash fake 1536-dim vector** (122-142); `health()` returns true if key non-empty only (167-169) | env / DB |
| Gemini | `gemini.py` | `GEMINI_API_KEY` | yes | no | 30s | maps assistant→model, system→systemInstruction | env / DB |
| Claude | `claude.py` | `ANTHROPIC_API_KEY` | yes | no | — | `max_tokens=4096` (34) | env / DB |
| OpenRouter | `openrouter.py` | `OPENROUTER_API_KEY` | yes | no | — | referer `https://viptant.ai`, title `Viptant AI Platform` (31-32) | env / DB |
| DeepSeek | `deepseek.py` | `DEEPSEEK_API_KEY` | yes | no | — | default `deepseek-chat` (27) | env / DB |
| Mistral | `mistral.py` | `MISTRAL_API_KEY` | yes | no | — | default `mistral-large-latest` (26) | env / DB |
| Ollama | `ollama.py` | `OLLAMA_API_KEY` + `OLLAMA_BASE_URL` (default localhost:11434) | yes | no | — | default `llama3` (27) | env / DB |

### Image/multimodal providers
`blackforestlabs.py:101`, `stability.py:126`, `replicate.py:113` (dummy `edit` at 107), `pollinations.py:70` (default `flux`), `openai_images.py:119` (registered as `"openai"`), `ideogram.py:92`, `huggingface.py:71`, `google_imagen.py:85` (registered as `"google"`, default `imagen-3.0-generate-002`), `fal.py:121`, `cloudflare.py:70`, `together.py:87`. Keys resolved at call time by `ai/agents/image/provider_router.py::_get_key` (267-318: env → user key → org key, decrypted).

### Gateway wiring (`ai/gateway/coordinator.py`)
- `__init__` hardcodes 8 provider instances (33-42).
- `_get_provider_adapter` (44-139): user-level key → org-level key → env; adapter map 103-112; **unknown provider defaults to GroqProvider (114)**; `AIProvider.base_url` overrides instance base_url (115, 133-134).

**Provider verification status: NOT RUNTIME VERIFIED for every provider.** No live call was made during this audit (credentials not validated, tests mock all adapters). Presence of an adapter does not imply working integration.

---

## 3.2 Routing & registry

### Implemented (real)
- `ai/router/engine.py`: `ModelRouter.route` seeds the registry (`ModelRegistryManager.seed_default_models`), filters `is_healthy == True`, skips Redis-blacklisted models/providers, accepts strategy/task_type/min_context_window/environment/load_balancer.
- `ai/registry/manager.py`: seeds hardcoded defaults when empty (e.g. `groq/openai/gpt-oss-120b` ctx 131072, in 0.1500/out 0.2000/1M, priority 11; `groq/llama-3.3-70b-versatile` 0.5900/0.7900, priority 10).
- `coordinator.py`: candidates from model kwarg → `AIModelRegistry` lookup else router.route (621-643); `max_retries=3` with exponential backoff (666-772); on exhausted retries → blacklist model TTL 300s (775) + `is_healthy=False` (777); routing/failover logs to `AIRoutingLog`/`AIFailoverEvent` (393-493).
- `models/router.py`: `AIRoutingPolicy` (scope global/org/dept/user/environment, default strategy `balanced`), `AIRoutingLog`.
- `services/ai/model_router_service.py`: `route_request` with `preferred_provider or "openai"`, per-provider default model table, `RouterPolicy.can_route`, publishes `ModelFailoverTriggered`/`ModelRouted`.

### Issues
| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| RTR-01 | MEDIUM | Fallback default provider is hardcoded Groq (`adapter_cls = adapters.get(..., GroqProvider)`); unknown providers silently route to Groq | `coordinator.py:114` |
| RTR-02 | MEDIUM | Provider health check is key-presence only for Groq (returns true if key string non-empty) → routing decisions based on non-verification | `groq.py:167-169` |
| RTR-03 | MEDIUM | `/ai/providers/{name}/models` returns a hardcoded 6-model catalog, falling back to the full list for unknown provider — ignores DB registry | `routes/ai.py:77-86` |
| RTR-04 | LOW | `POST /ai/router/simulate` exists (`routes/router.py:190-191`) — simulation endpoint in production routes | `routes/router.py` |
| RTR-05 | INFO | Default model constants: `services/ai/constants.py` (`DEFAULT_MODEL_PER_PROVIDER`, `MODEL_PRICING_PER_1K`, `DEFAULT_EMBEDDING_MODEL=text-embedding-3-small` dim 1536) |

---

## 3.3 Prompt rendering & variable rendering

- `services/ai/prompt_service.py` + `services/prompt.py`: real template rendering with variable substitution (tests exist: `test_ai_prompts_extended.py`, `test_prompts_v1.py`).
- Default model fallback `gemini-1.5-flash` (`services/prompt.py:780`), **fallback `"Sample execution response."` (789)**, provider `"google"` (790), token split 60/40 (813-814). `EvaluationService` returns hardcoded scores 0.95/0.92/0.94 (946-966). ⚠️ These are production-path simulations.

---

## 3.4 RAG audit

### Real path (used by routes)
- `routes/knowledge.py` `/search` (852-892): `AIGateway.embeddings` → `VectorStore.semantic/hybrid/keyword_search` + `mmr_rerank`; `/rag` (895-918) → `RAGEngineService`.
- `services/rag_engine.py` (16-262): embed → hybrid search → MMR rerank → context build (12,000-char budget at 107) → `gateway.chat` (174) → citation regex `[Source N]` (192-200) → confidence heuristic (207-222) → hallucination-risk heuristic (264-291) → `KnowledgeSearchHistory` log (228-242).
- `services/vector_store.py`: pure-Python `_cosine_similarity`; `apply_filters` enforces `DocumentChunk.organization_id == org` + `KnowledgeDocument.deleted_at IS NULL` (255).
- `services/knowledge_service.py`: char-based chunking (500/100), upload embeds via `AIGateway`.
- `models/knowledge.py`: `DocumentChunk` (sha256 content_hash 199-202), `DocumentChunkEmbedding` `SafeVector(1536)` (223).

### Stub / fabricated components
| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| RAG-01 | HIGH | `VectorSearchService.search_vector_index` fabricates random chunk/document UUIDs, score `0.92-(i*0.05)`, canned snippet text; no DB access | `services/knowledge/vector_search_service.py:40-52` |
| RAG-02 | HIGH | `AGUIExecutionService.execute` returns mock payload with hardcoded `gpt-4o` and fake Card UI schema | `services/ai/agui_execution_service.py:66-76` |
| RAG-03 | MEDIUM | `ai/rag/pipeline.py`: `ingest_document` returns True (17), `query_with_context` returns empty (24) — TODO stubs | `ai/rag/pipeline.py` |
| RAG-04 | MEDIUM | `ai/retrieval/retriever.py`: `retrieve` returns `[]` (17) | `ai/retrieval/retriever.py` |
| RAG-05 | MEDIUM | `ai/embeddings/embedder.py`: `embed_text`/`embed_batch` return `[0.0]*1536` zeros (17,24) | `ai/embeddings/embedder.py` |
| RAG-06 | MEDIUM | `document_ingestion_service.py`: `ingest_document` estimates chunk count and returns `INDEXED` without persisting (36-82) | `services/knowledge/document_ingestion_service.py` |
| RAG-07 | LOW | `services/ai/rag_service.py:search` falls back to dummy similarity 0.85 ("SQLite fallback", 116-119) | `services/ai/rag_service.py` |
| RAG-08 | MEDIUM | Vector "index" is JSONB `vector` column + Python cosine scan — no pgvector index; embedding model consistency depends on registry defaults | `services/vector_store.py`; `models/knowledge.py` |

Tenant isolation in RAG: enforced in the route-level path (`apply_filters` org filter + deleted filter). No data-leak test exists beyond route tests.

---

## 3.5 Memory audit

- `ai/memory/memory.py`: `ConversationalMemoryBuffer` max 20 messages, **in-memory only** (no persistence).
- `models/memory.py`: `AgentMemory`, `AgentSessionSummary`, `OrganizationMemory` (brand_voice, company_facts, audience, guidelines, preferences).
- `services/memory_manager.py`: `write_memory` upsert by agent_id+key+org; tiers short/long/org; `read_memory`, `clear_session_memory`.
- `services/ai/memory_service.py`: cache-keyed window; `MemoryPolicy.can_access`; uses `unittest.mock` at 192-193.
- `routes/memory.py`: org memory POST/GET, session short-term (145-194), agent long-term (197-244).

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| MEM-01 | MEDIUM | No retention/expiry for persistent memory; no max-size enforcement beyond buffer limit | `models/memory.py`, `services/memory_manager.py` |
| MEM-02 | MEDIUM | No security review for sensitive data written into memory (no PII mask on write path) | `services/memory_manager.py` |
| MEM-03 | LOW | Conversation memory cache default is a hardcoded dict (empty) | `services/ai/memory_service.py` |

---

## 3.6 Usage & cost audit

### Implemented
- `ai/cost/cost_tracker.py` — hardcoded `MODEL_PRICING` per-token (gpt-4o 0.000005/0.000015, claude-3-5-sonnet 0.000003/0.000015, default 0.000002/0.000006).
- `services/ai/ai_usage_service.py` — pricing from `MODEL_PRICING_PER_1K` (default in 0.0025 / out 0.01), publishes `AIUsageRecorded`.
- `models/ai_usage.py` — `AITokenUsage` (org+user FKs, token counts, `cost_usd Numeric(10,6)`, status, retry_count).
- `coordinator.py` `_calculate_cost` uses registry per-1M prices (141-153); `_log_usage` writes `AITokenUsage`+`AIRequest`+`AIUsage`+`AICost`+`AILog`+`AITrace` (155-391); `_check_and_seed_limit` seeds org limits 100.00/60rpm/50k tpm (495-517); `_update_credit_usage` (519-528).

### Issues
| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| COST-01 | HIGH | **Double-charge risk**: coordinator logs usage per retry attempt without dedup; retries/fallbacks can record multiple `AITokenUsage` rows for one logical request (no idempotency key) | `coordinator.py:155-391,666-772` |
| COST-02 | HIGH | Hardcoded/fabricated costs: image `cost_usd = 0.04` (`ai/agents/image/executor.py:184`), compare-image `0.04` (`routes/ai.py:2529`), prompt eval `0.0003` (`services/prompt.py:966`), vision logs fixed 100/100 (`coordinator.py:1304-1317`), json_output 50/50 (1438-1451), embeddings charged by word count (1174-1177) | evidence per line |
| COST-03 | MEDIUM | Streaming token accounting = word counts (`services/conversation.py:234-242`) — inaccurate billing | `services/conversation.py` |
| COST-04 | MEDIUM | `seed_dummy_usages` inserts 120 synthetic usage rows (invoked from usage list and analytics dashboard) — pollutes live accounting data | `routes/ai.py:1092-1147,1156,2612` |
| COST-05 | MEDIUM | Multiple pricing tables disagree (`cost_tracker.py`, `constants.py`, registry prices, per-1M vs per-1K) → inconsistent cost figures | files cited |

---

## 3.7 Streaming & AGUI audit

- `ai/runtime/streaming_runtime.py` — real SSE lifecycle (agent_start, status, context_ready, plan, tool_call, tool_result, token, reflection, evaluation, done, error); uses `AIGateway.stream` with fallback to `chat` (222-239).
- `routes/chat.py` `/{id}/stream` (606-651) SSE endpoint; voice endpoint calls Groq whisper directly (866-888).
- `services/conversation.py::stream_response` (145-263) SSE generator.
- `AGUIExecutionService` — **mock** (see RAG-02).

| ID | Sev | Finding | Evidence |
|----|-----|----------|---------|
| STR-01 | MEDIUM | Streaming tokens/cost computed from word splits, not provider usage payloads | `services/conversation.py:234-242` |
| STR-02 | MEDIUM | No disconnect/cancellation stress tests; connection-leak risk not verified | no test coverage |
| STR-03 | MEDIUM | AGUI execution is mocked in the production service layer | `agui_execution_service.py:66-76` |

---

## 3.8 Error handling matrix (from coordinator + providers)

| HTTP/condition | Behavior | Notes |
|---|---|---|
| 401/403 | raise → retry | retried; no distinction between auth failure and transient error → key invalidation not triggered |
| 404/409 | raise → retry | model/provider not found retried pointlessly |
| 408/429 | raise → retry w/ backoff | 429 should honor Retry-After — not implemented |
| 500/502/503/504 | raise → retry w/ exp backoff | max_retries=3 |
| Network failure / timeout | raise → retry | timeout 30s/120s gateway |
| Malformed response | exception → retry | wrapped |
| Streaming disconnect | generator exit | partial output kept; usage approximated |
| Context length exceeded | raise → retry | **no prompt-trimming fallback** — retried as-is |

Correct behavior gaps: 429 Retry-After ignored; 401/403 retried (wastes quota); no context-window-aware fallback; failed requests DO get usage/cost recorded (retry_count tracked but no "failed request = no charge" policy enforced).

---

## 3.9 Verdict

| Sub-area | Status |
|---|---|
| Providers | 🟡 PARTIAL — 8 adapters, all NOT RUNTIME VERIFIED; Groq embeddings fake |
| Routing | 🟡 PARTIAL — real retry/blacklist/failover; hardcoded defaults/fallback |
| Credential resolution | 🟡 PARTIAL — 3-tier resolution works; org-scope gap in user keys |
| RAG | 🟡 PARTIAL — route path real; service layer fabricated |
| Memory | 🟡 PARTIAL — buffer in-memory; no retention/security review |
| Usage/Cost | 🔴 RISK — double-charge risk; hardcoded costs; synthetic seeding |
| Streaming | 🟢/🟡 — real SSE; approximate accounting; no stress tests |
| AGUI | 🔴 MISSING — mocked |