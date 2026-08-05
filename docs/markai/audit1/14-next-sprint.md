# Enterprise Source Code Audit - Recommended Next Sprint

## Next Sprint Backlog

Ordered by priority and impact.

### 1. Fix Hardcoded JWT Secrets (Priority: Critical)
- **Problem**: Default `SECRET_KEY` is hardcoded as a string fallback in Pydantic settings.
- **Action**: Remove the default string value in [core/config.py](file:///d:/markai/apps/api/src/api/core/config.py#L61-L64) to force configuration validation failures if the variable is missing from environment.
- **Estimate**: 1 Story Point

### 2. Implement Real Background Queue Consumption (Priority: High)
- **Problem**: The background worker entry point in [workers/worker.py](file:///d:/markai/apps/api/src/api/workers/worker.py#L12) is a `pass` stub.
- **Action**: Implement task listener triggers connecting to Celery's message broker. Update deployment manifests to run Celery as a separate container daemon.
- **Estimate**: 5 Story Points

### 3. Replace Simulated RAG with PostgreSQL pgvector (Priority: High)
- **Problem**: Vector search relies on a simulated hashing mechanism that creates deterministic MD5 vectors in [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L103-L123), rather than querying actual vector DBs.
- **Action**: Configure pgvector extensions on the database and update [ai/vector/vector_store.py](file:///d:/markai/apps/api/src/api/ai/vector/vector_store.py) to perform real vector queries using an embedding provider (like OpenAI or local SentenceTransformers).
- **Estimate**: 8 Story Points

### 4. Implement OAuth & Real Social Publisher Adapters (Priority: High)
- **Problem**: The publisher adapters (LinkedIn, Twitter, Facebook, Instagram, YouTube, Threads) in [helpers.py](file:///d:/markai/apps/api/src/api/ai/agents/social/helpers.py#L367-L514) return mocks.
- **Action**: Implement OAuth token injection workflows and connect publishers to real external APIs (e.g. using `tweepy` for X/Twitter, or Graph API for Facebook/Instagram).
- **Estimate**: 13 Story Points

### 5. Transition Provider Clients to Async (Priority: Medium)
- **Problem**: outbound provider HTTP calls block event loops since they use synchronous clients.
- **Action**: Replace `httpx.Client()` with `httpx.AsyncClient()` inside [ai/providers/](file:///d:/markai/apps/api/src/api/ai/providers/) files and refactor endpoints to use `await` calls.
- **Estimate**: 5 Story Points

### 6. Optimize Database Indices (Priority: Medium)
- **Problem**: Foreign keys lack indexing, causing performance bottlenecks as datasets grow.
- **Action**: Add SQLAlchemy index annotations on all foreign keys across models, and create corresponding Alembic migrations.
- **Estimate**: 3 Story Points

### 7. Code Split Large Frontend Bundles (Priority: Low)
- **Problem**: Eagerly loaded visual packages (like recharts and React Flow) slow down LCP.
- **Action**: Refactor frontend routes to use Next.js dynamic imports (`next/dynamic`) with loading indicators.
- **Estimate**: 2 Story Points
