# Sprint 3: AI Platform (LLM Gateway, Prompt Library, AI Chat, Conversation History) - Implementation Plan

This plan details the architecture and implementation of the AI Platform module. This sprint establishes a centralized AI interface featuring a unified LLM Gateway, reusable Prompt Library (with versioning), Chat session histories, and routing rules supporting multiple model providers (OpenAI, Gemini, Claude).

## User Review Required

> [!IMPORTANT]
> **LLM Gateway & Provider Integrations:**
> - The backend will implement a modular `LLMGateway` and `ModelRouter` which parses prompts and routes requests to the designated LLM provider.
> - For development/demonstration purposes when API keys are not supplied in `.env`, the gateway will fail gracefully or fall back to a mock AI response detailing the selected model and system routing path.
> - Multi-tenant isolation is maintained: Prompts and Conversation histories are strictly isolated using `organization_id`.

## Proposed Changes

### 1. Database Schema

We will define three new tables:

#### [NEW] [apps/api/src/api/models/prompt.py](file:///d:/markai/apps/api/src/api/models/prompt.py)
Prompt templates that can be customized and versioned.
- `name`: String (255)
- `content`: Text (template with `{variables}`)
- `version`: Integer, default 1
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/conversation.py](file:///d:/markai/apps/api/src/api/models/conversation.py)
Represents a chat session.
- `title`: String (255)
- `user_id`: ForeignKey to users
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/message.py](file:///d:/markai/apps/api/src/api/models/message.py)
Stores conversation history.
- `conversation_id`: ForeignKey to conversations
- `role`: String (50) - `user`, `assistant`, `system`
- `content`: Text
- `model_used`: String (100) - e.g. `gpt-4o`, `gemini-1.5-flash`, `claude-3-5-sonnet`

---

### 2. LLM Gateway & Core AI Logic

#### [NEW] [apps/api/src/api/services/llm.py](file:///d:/markai/apps/api/src/api/services/llm.py)
Implements:
- `ModelRouter`: Directs prompts to different endpoints.
- `LLMGateway`: Connects to LangChain/LangGraph or direct API calls with fallback mock generators when credentials are not configured.

---

### 3. API Endpoints (v1)

We will implement routers under `/api/v1/ai/`:
- **Prompt Library:** `/api/v1/ai/prompts/` (`GET`, `POST`, `DELETE`)
- **Chat Conversations:** `/api/v1/ai/conversations/` (`GET`, `POST`, `DELETE`)
- **Chat Messages / Gateway:** `/api/v1/ai/conversations/{id}/messages` (`GET`, `POST` - triggers LLM generation)

---

### 4. Frontend UI Dashboard

We will implement an interactive AI playground in Next.js:
- **`apps/web/src/app/dashboard/ai/page.tsx`**: Features a split screen. The left panel shows conversation history sessions and Prompt template selection. The right panel displays the active messaging thread, model selection dropdown, and chat controls.

---

## Verification Plan

### Automated Tests
- Write test file `apps/api/tests/test_ai.py` to assert prompt creation/versioning, conversation histories, and LLM gateway responses.
- Run: `poetry run pytest tests/test_ai.py`
