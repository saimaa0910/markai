# Enterprise Source Code Audit - AI Runtime Audit

## AI Runtime Features Summary

| Feature / System | Status | Evidence | Files |
| :--- | :--- | :--- | :--- |
| **Agent Runtime** | ✓ Fully Implemented | Coordinates context building, planning, tool execution, final response synthesis, reflection, evaluation, and memory persistence in a structured execution pipeline. | [agent_runtime.py](file:///d:/markai/apps/api/src/api/ai/runtime/agent_runtime.py) |
| **Agent Planner** | ✓ Fully Implemented | Generates multi-step execution plans containing specific tasks and parameter schemas for allowed tools. | [planner.py](file:///d:/markai/apps/api/src/api/ai/planner/planner.py) |
| **Tool Registry & Executor** | ✓ Fully Implemented | `ToolRegistry` lists tools. `ToolExecutor` executes tool routines (`crm_tool`, `knowledge_tool`, `workflow_tool`, `calculator_tool`, etc.). | [registry.py](file:///d:/markai/apps/api/src/api/ai/tools/registry.py) |
| **AI Gateway** | ✓ Fully Implemented | Central coordinator with provider key decryption, routing, quota controls, token cost calculation, and logging. | [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py) |
| **Provider Adapters** | ✓ Fully Implemented | Adapters route calls to Groq, Claude, Gemini, OpenAI, etc. However, all image generation/publishing endpoints are mock stubs. | [openai.py](file:///d:/markai/apps/api/src/api/ai/providers/openai.py), [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py) |
| **RAG Ingestion & Search** | 🟡 Partial | Chunckers, cleaners, and parsers exist, but retrieval relies on simulated embeddings MD5 hashes and in-memory similarities instead of pgvector indexes. | [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L103-L123), [vector_store.py](file:///d:/markai/apps/api/src/api/ai/vector/vector_store.py) |
| **Memory Management** | ✓ Fully Implemented | Connects short-term session memory and long-term agent memory. Reads/writes are persisted in the database. | [memory_manager.py](file:///d:/markai/apps/api/src/api/services/memory_manager.py), [memory.py](file:///d:/markai/apps/api/src/api/models/memory.py) |
| **Reflection & Evaluation** | ✓ Fully Implemented | `ai_reflector` critiques responses. `ai_evaluator` grades runs across multiple dimensions and stores results in `agent_evaluations`. | [reflection.py](file:///d:/markai/apps/api/src/api/ai/reflection/reflection.py), [evaluator.py](file:///d:/markai/apps/api/src/api/ai/evaluation/evaluator.py) |
| **Cost & Token Tracking** | ✓ Fully Implemented | Gateway calculates USD cost based on token registry prices per 1M tokens. Updates quotas and credit usage tables. | [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py#L141-L153) |
| **Retries & Failovers** | ✓ Fully Implemented | Implements backoff retries (up to 3 times) and model blacklisting, automatically failing over to the next routing candidate on errors. | [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py#L769-L806) |

------------------------------------------------------------

## Detailed Findings

### 1. Unified Agent Execution Loop
The `AgentRuntime.execute()` function in [agent_runtime.py](file:///d:/markai/apps/api/src/api/ai/runtime/agent_runtime.py#L71-L301) orchestrates the runtime lifecycle:
1. Logs step start to `agent_logs`.
2. Resolves prompt template name and builds context string.
3. Requests execution plan from `AgentPlannerService`.
4. Validates tool permissions and executes allowed tools via `ToolExecutor`.
5. Re-builds context incorporating tool results.
6. Calls `AIGateway.chat` to compile final agent response.
7. Triggers critique verification via `ai_reflector`.
8. Saves quality grades using `ai_evaluator`.
9. Appends session state variables via `MemoryManager.write_memory`.
10. Saves final `AgentRun` state to Postgres/SQLite.

### 2. Provider Routing
The model router engine in [router/engine.py](file:///d:/markai/apps/api/src/api/ai/router/engine.py) ranks provider models based on rules:
- **cost**: routes to cheap models (e.g. `llama-3-8b-instruct` or `gemini-2.5-flash`).
- **speed**: routes to fast endpoints.
- **quality**: routes to pro models (e.g. `llama-3.3-70b-versatile` or `claude-3-5-sonnet`).

### 3. RAG / Embeddings Simulation
The retrieval system is currently simulated:
- **Embeddings**: In [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L103-L123), `embeddings` computes a deterministic 1536-dimensional vector by taking the MD5 hash of lowercase words, scaling them, and normalizing the vector:
  ```python
  for i, word in enumerate(words):
      h = int(hashlib.md5(f"{word}:{i % 10}".encode("utf-8")).hexdigest(), 16)
      idx = h % dim
      val = ((h >> 16) % 10000) / 10000.0 - 0.5
      vec[idx] += val
  ```
- **Similarity Search**: Cosine similarity is calculated directly in memory without indices:
  ```python
  sim_score = KnowledgeService._cosine_similarity(query_embedding, chunk.embedding)
  ```
This is a fake neural embeddings method. A real embedding service (like OpenAI's text-embedding-3 or HuggingFace TEI) must be integrated for production use.
