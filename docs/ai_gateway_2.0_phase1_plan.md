# AI Gateway 2.0: Phase 1 (Architecture, Folder Structure, Database, API Design) - Implementation Plan

This plan details the foundation architecture, files structure, and database models for **Phase 1** of Viptant's AI Gateway 2.0.

---

## 1. Directory Structure

We establish the gateway layouts under `apps/api/src/api/ai/`:

```
apps/api/src/api/ai/
├── gateway/             # Central gateway coordinator
├── providers/           # Base provider interface and adapter subclasses
├── router/              # LLM routing engine based on registry rules
├── registry/            # Centralized model registry
├── prompts/             # Prompt library management
├── conversations/       # Conversations and messages management
├── embeddings/          # Embeddings generator
├── rag/                 # RAG context retrivers
├── knowledge/           # Document processors & vector indexing
├── usage/               # Billing and usage statistics tracking
├── analytics/           # Analytics aggregates
├── moderation/          # Input/output safety filters
├── tools/               # Function calling schemas
├── workflows/           # Orchestration workflows
├── memory/              # Chat context/memory utility
├── schemas/             # Pydantic validation schemas
├── services/            # Application orchestration services
├── repositories/        # SQLAlchemy data repositories
└── api/                 # FastAPI routes (v1 endpoints)
```

---

## 2. Database Schema Design

*   **`ai_models_registry`**: Global/Tenant model metadata.
*   **`ai_routing_rules`**: Links specific request types (chat, content, vision, embeddings, json) to models.
*   **`ai_token_usages`**: Track consumption metrics.
*   **`knowledge_documents`**: Stores files metadata.
*   **`document_chunks`**: Stores raw text fragments and SafeVector embeddings.
*   **`prompts`**: Extended with `category`, `tags`, and `is_shared` columns.
*   **`messages`**: Extended with `provider_used`, `latency_ms`, `prompt_tokens`, `completion_tokens`, and `cost_usd` fields.

---

## 3. Verification Plan

*   **Pytest test suite**: Run database validation tests in `tests/test_ai_gateway_db.py`.
