# AI Gateway 2.0: Phase 1 (Architecture & Database Schema) - Walkthrough

This document records the completion of **Phase 1** of Viptant's AI Gateway 2.0.

---

## 1. Directory Structure

Created all new database models under `apps/api/src/api/models/` and established the package layout for the gateway at `apps/api/src/api/ai/`.

---

## 2. Implemented Database Schema

We have defined the core database models using SQLAlchemy 2.0 to support centralized model metadata registry, token usages auditing, and document vector indexing:

### New Tables:
1.  **`ai_models_registry`**: Stores properties of model providers (Groq, OpenRouter, OpenAI, Claude, Gemini), capabilities flags, token costs cards, average latency, and health statuses.
2.  **`ai_routing_rules`**: Stores routing rules mapped by request types (chat, content, vision, embeddings, json) pointing to registry entries. Supports tenant-level overrides.
3.  **`ai_token_usages`**: Logs prompt and completion tokens, dollar costs card calculations, response speed latency, and call outcomes per user/tenant transaction.
4.  **`knowledge_documents`**: Stores files metadata (`pdf`, `docx`, `csv`, `md`, `url`).
5.  **`document_chunks`**: Stores raw text fragments and 1536-dimensional embeddings. Implements custom SQLAlchemy `SafeVector` TypeDecorator.

### Modified Tables:
*   **`prompts`**: Added `category`, `tags`, and `is_shared` columns to prompt templates.
*   **`messages`**: Added `provider_used`, `latency_ms`, `prompt_tokens`, `completion_tokens`, and `cost_usd` fields to enable conversation auditing.

---

## 3. Database Migrations

*   Generated migrations: `alembic/versions/2e87819f588c_add_ai_gateway_phase1.py`.
*   Cleaned and executed migrations to `test_db.db`:
    ```bash
    Running upgrade 37fd075bd0de -> 2e87819f588c, add_ai_gateway_phase1
    ```

---

## 4. Verification Results

Wrote integration tests in `apps/api/tests/test_ai_gateway_db.py`. All tests passed successfully:

```bash
platform win32 -- Python 3.13.7, pytest-8.4.2, pluggy-1.6.0
collected 9 items

tests\test_ai.py .                                                       [ 11%]
tests\test_ai_gateway_db.py .                                            [ 22%]
tests\test_auth.py ..                                                    [ 44%]
tests\test_campaigns.py .                                                [ 55%]
tests\test_crm.py .                                                      [ 66%]
tests\test_generator.py .                                                [ 77%]
tests\test_main.py ..                                                    [100%]

======================= 9 passed, 13 warnings in 9.54s ========================
```
