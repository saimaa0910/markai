# EAIMOS AI GATEWAY — REMAINING WORK & PRODUCTION READINESS ROADMAP

This document outlines the priority engineering roadmap to elevate the EAIMOS AI Gateway from its current functional state to production-ready enterprise tier.

---

## 1. Critical Priority Fixes (P0 — Blocker for Production Scale)

1. **Migrate Circuit Breaker State to Distributed Redis**:
   - **Problem**: `AIGateway._breaker` is an in-memory dictionary isolated to each worker process.
   - **Fix**: Move circuit breaker failure counters and state transitions to Redis using atomic Lua scripts or `redis-py` pipeline commands.

2. **Migrate Synchronous Media Providers to Async `httpx`**:
   - **Problem**: Media providers (`fal.py`, `stability.py`, `ideogram.py`, `replicate.py`, `blackforestlabs.py`, `together.py`, `pollinations.py`, `cloudflare.py`) use blocking `requests` and `time.sleep()`, stalling the FastAPI async event loop.
   - **Fix**: Refactor all media providers to use `httpx.AsyncClient` and async polling with `asyncio.sleep()`.

3. **Fix Groq Embeddings Endpoint Mismatch**:
   - **Problem**: `GroqProvider.embeddings()` hits `https://api.groq.com/openai/v1/embeddings` with OpenAI's `text-embedding-3-small`, which Groq does not serve.
   - **Fix**: Route embeddings requests exclusively to verified embeddings providers (OpenAI, Mistral, Ollama) or return explicit capability errors.

4. **Offload Rate Limiting from PostgreSQL to Redis**:
   - **Problem**: `RateLimitService` writes every attempt to PostgreSQL `RateLimitLog`, causing database write contention under 20k concurrent users.
   - **Fix**: Implement sliding-window rate limiting using Redis Sorted Sets (`ZADD`, `ZREMRANGEBYSCORE`, `ZCARD`).

5. **Eliminate Mock Usage Injection in Production Routes**:
   - **Problem**: `seed_dummy_usages()` in `ai.py` inserts fake rows into `AITokenUsage` when tables are empty, corrupting real analytics.
   - **Fix**: Guard dummy seeding behind an explicit dev environment flag (`if settings.ENVIRONMENT == "development"`), and render proper empty-state UI in the frontend.

---

## 2. High Priority Improvements (P1 — Resilience, Security & Accuracy)

1. **Clean Up Dead Code & Unused Stub Files**:
   - **Tasks**:
     - Remove `apps/api/src/api/ai/embeddings/embedder.py` (which returns dummy zeros).
     - Remove `apps/api/src/api/ai/rag/pipeline.py` (which returns dummy dicts).
     - Consolidate `apps/api/src/api/ai/cost/cost_tracker.py` into `coordinator.py`.

2. **Replace Hardcoded String Matching in Routing Engine**:
   - **Problem**: `engine.py` uses heuristic string checks like `if "claude" in m.model_name or "gpt-4" in m.model_name`.
   - **Fix**: Add a `tags` array column to `AIModelRegistry` (e.g. `tags: ["reasoning", "coding", "fast"]`) and query database tags dynamically.

3. **Dynamic Latency Moving Average (EWMA)**:
   - **Problem**: Latency sorting in `fastest` strategy relies on static benchmark numbers.
   - **Fix**: Calculate an exponentially weighted moving average (EWMA) of actual request response times and update `AIModelRegistry.latency` in the background every 5 minutes.

4. **Connect Hardcoded Frontend Dashboard Elements**:
   - **Tasks**:
     - Replace hardcoded `MOCK_AUDITS` in `admin.tsx` with a live query to `/ai/security/audit`.
     - Replace static `radarData` and random `heatmapData` in `analytics.tsx` with aggregated hourly time-series data from `/ai/analytics/`.

---

## 3. Medium Priority Enhancements (P2 — Enterprise Features)

1. **Semantic Vector Memory Search**:
   - Add pgvector embedding generation to `AgentMemory` and `ConversationMemory` so agents can perform semantic similarity search across historical conversation sessions.

2. **Semantic Document Chunking**:
   - Replace character-based sliding window chunking in `KnowledgeService` with AST-aware markdown and token-aware semantic sentence splitters.

3. **Comprehensive Load & Stress Testing Suite**:
   - Build a Locust/k6 performance test harness simulating **20,000 concurrent active users** streaming responses across multiple providers to validate P99 latency and failover resilience.

---

## 4. Production Readiness Checklist Summary

- [ ] Distributed Redis Circuit Breakers
- [ ] Async HTTPX for all 16 Providers
- [ ] Redis Sorted-Set Rate Limiter
- [ ] Dead Stub Files Cleaned
- [ ] Mock Usage Seeder Disabled in Production
- [ ] Tag-Based Routing Engine
- [ ] EWMA Live Latency Tracking
- [ ] Frontend Mock Data Replaced with Real Endpoints
- [ ] 20,000 Concurrent User Load Test Passed
