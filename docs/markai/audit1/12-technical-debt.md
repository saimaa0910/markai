# Enterprise Source Code Audit - Technical Debt, Dead Code, and Duplicate Code

## Dead Code Findings
1. **Unused API Security file**: The file [api/security/security.py](file:///d:/markai/apps/api/src/api/security/security.py) contains token payload generator utilities. However, it is never imported or referenced in the repository. Instead, [api/core/security.py](file:///d:/markai/apps/api/src/api/core/security.py) handles all token creation.
2. **Duplicate Local Packages**: The `packages/` directory contains folders like `database`, `api-client`, `observability`, and `shared` which contain TypeScript stubs. The frontend Next.js application bypasses these packages, importing from local code libraries (e.g. `apps/web/src/services/api-client.ts`).
3. **Mock E2E Tests**: The E2E tests in [tests/e2e.test.ts](file:///d:/markai/tests/e2e.test.ts) is a simple skeleton placeholder containing no real E2E assertion logic.

------------------------------------------------------------

## Duplicate Code Findings
1. **Duplicate Models Mappings**: `AITokenUsage` (historical token usage) and `AIUsage` (newer usage logging) tables map the exact same fields (`organization_id`, `user_id`, `provider`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`, `latency_ms`, `status`). Both tables are updated simultaneously in the Gateway logging flow.
2. **FastAPI Route Controllers**: Database CRUD routines are duplicated across controllers (e.g., `routes/generator.py` implements custom delete query blocks instead of reusing the generic base repository).

------------------------------------------------------------

## Technical Debt Classification

### Critical Priority (Must address before deployment)
- **Hardcoded Secret Key**: Default `SECRET_KEY` is hardcoded inside [core/config.py](file:///d:/markai/apps/api/src/api/core/config.py#L61-L64) and will be used if the environment variable is missing.

### High Priority (Address next sprint)
- **Simulated RAG & Embeddings**: The vector search computes MD5 hashes of words in [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L103-L123) and performs cosine similarity in memory, rather than querying actual database pgvector extensions.
- **Queue worker Consumption loop**: Celery workers are stubbed in [workers/worker.py](file:///d:/markai/apps/api/src/api/workers/worker.py) with a `pass` statement, meaning no tasks are popped from the queue in production.
- **OAuth and Publisher Stubs**: Publisher adapters (LinkedIn, Twitter, Facebook, Instagram, YouTube, Threads) in [helpers.py](file:///d:/markai/apps/api/src/api/ai/agents/social/helpers.py#L367-L514) return mocked statuses and stubs. They must be integrated with real OAuth providers.

### Medium Priority
- **Blocking outbound HTTP requests**: Upstream provider requests in [ai/providers](file:///d:/markai/apps/api/src/api/ai/providers/) use synchronous `httpx.Client` inside FastAPI routes, which blocks the main thread pool.
- **Foreign Key Indexing**: Database schemas lack indices on several foreign keys, causing table scans on heavy workloads.

### Low Priority
- **Webpack Bundle Size**: Eagerly loaded chart modules (`recharts`) and diagram libraries should be dynamically code-split on the frontend.
