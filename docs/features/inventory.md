# Feature Inventory

This document presents a complete inventory of all features implemented across the `markai` codebase. Every feature listed below is derived directly from existing source code files.

---

## Implemented Features Catalog

### 1. User Authentication & Session Management
- **Description**: Secure email/password login, JWT access & refresh token rotation, user registration, profile retrieval, password hash validation.
- **Backend File(s)**: [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py), [security.py](file:///d:/markai/apps/api/src/api/core/security.py)
- **Frontend File(s)**: [login/page.tsx](file:///d:/markai/apps/web/src/app/auth/login/page.tsx), [register/page.tsx](file:///d:/markai/apps/web/src/app/auth/register/page.tsx), [auth.ts](file:///d:/markai/apps/web/src/store/auth.ts)
- **Database Table(s)**: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`
- **API Routes**: `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`
- **Dependencies**: PyJWT, passlib[bcrypt]
- **Status**: Implemented
- **Tests**: [test_auth.py](file:///d:/markai/apps/api/tests/test_auth.py)
- **Owner Module**: `Auth`

---

### 2. Multi-Tenant Organization & Role-Based Access Control (RBAC)
- **Description**: Organization tenant creation, membership invitation, role assignment (`OWNER`, `ADMIN`, `MEMBER`, `GUEST`), permission check dependencies.
- **Backend File(s)**: [organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py), [deps.py](file:///d:/markai/apps/api/src/api/core/deps.py)
- **Frontend File(s)**: [settings/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/settings/page.tsx)
- **Database Table(s)**: `organizations`, `user_organizations`
- **API Routes**: `GET /api/v1/organizations`, `POST /api/v1/organizations`, `GET /api/v1/organizations/{id}/members`, `POST /api/v1/organizations/{id}/members`
- **Dependencies**: SQLAlchemy ORM
- **Status**: Implemented
- **Tests**: [test_phase2_auth_orgs.py](file:///d:/markai/apps/api/tests/test_phase2_auth_orgs.py)
- **Owner Module**: `Organizations`

---

### 3. AI Gateway 2.0 Multi-Provider Proxy & SSE Streaming
- **Description**: Unified proxy routing LLM calls across OpenAI, Anthropic Claude, Google Gemini, Groq, and OpenRouter with Server-Sent Events (SSE) streaming and real-time token tracking.
- **Backend File(s)**: [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py), [providers/](file:///d:/markai/apps/api/src/api/ai/providers/)
- **Frontend File(s)**: [ai/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/ai/page.tsx), [ai.ts](file:///d:/markai/apps/web/src/store/ai.ts)
- **Database Table(s)**: `ai_providers`, `ai_model_registry`, `ai_usage_logs`
- **API Routes**: `POST /api/v1/ai/generate`, `POST /api/v1/ai/stream`, `GET /api/v1/ai/models`, `GET /api/v1/ai/providers`
- **Dependencies**: `httpx`, `asyncio`
- **Status**: Implemented
- **Tests**: [test_ai_gateway.py](file:///d:/markai/apps/api/tests/test_ai_gateway.py), [test_ai_gateway_stream.py](file:///d:/markai/apps/api/tests/test_ai_gateway_db.py)
- **Owner Module**: `AI Gateway`

---

### 4. Intelligent LLM Enterprise Router
- **Description**: Dynamic routing engine prioritizing model selection by minimum cost, lowest latency, highest capability score, or fallback chains.
- **Backend File(s)**: [engine.py](file:///d:/markai/apps/api/src/api/ai/router/engine.py), [router.py](file:///d:/markai/apps/api/src/api/routes/router.py)
- **Frontend File(s)**: [ai/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/ai/page.tsx)
- **Database Table(s)**: `ai_routing_rules`
- **API Routes**: `GET /api/v1/ai/routing/rules`, `POST /api/v1/ai/routing/rules`, `POST /api/v1/ai/routing/resolve`
- **Dependencies**: SQLAlchemy, Pydantic
- **Status**: Implemented
- **Tests**: [test_ai_router_phase1b.py](file:///d:/markai/apps/api/tests/test_ai_router_phase1b.py)
- **Owner Module**: `AI Router`

---

### 5. AI Security Pipeline & Threat Scanner
- **Description**: Multi-stage pre-generation and post-generation scanner checking for prompt injection, toxic content, PII data leakage, and system prompt override attempts.
- **Backend File(s)**: [pipeline.py](file:///d:/markai/apps/api/src/api/ai/security/pipeline.py), [security.py](file:///d:/markai/apps/api/src/api/routes/security.py)
- **Frontend File(s)**: [settings/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/settings/page.tsx)
- **Database Table(s)**: `security_events`, `security_policies`
- **API Routes**: `POST /api/v1/security/scan`, `GET /api/v1/security/events`, `GET /api/v1/security/policies`
- **Dependencies**: Regex, standard string scanners
- **Status**: Implemented
- **Tests**: [test_ai_security_phase1c.py](file:///d:/markai/apps/api/tests/test_ai_security_phase1c.py)
- **Owner Module**: `Security`

---

### 6. Prompt Management System & Playground
- **Description**: Variable-interpolated prompt template creation, version control, tagging, and interactive testing playground.
- **Backend File(s)**: [prompt.py](file:///d:/markai/apps/api/src/api/services/prompt.py), [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py)
- **Frontend File(s)**: [prompts/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/prompts/page.tsx)
- **Database Table(s)**: `prompts`, `prompt_versions`, `prompt_executions`
- **API Routes**: `GET /api/v1/ai/prompts`, `POST /api/v1/ai/prompts`, `POST /api/v1/ai/playground/run`
- **Dependencies**: Jinja2 / string formatting
- **Status**: Implemented
- **Tests**: [test_ai_prompts_extended.py](file:///d:/markai/apps/api/tests/test_ai_prompts_extended.py)
- **Owner Module**: `Prompts`

---

### 7. AI Agent Execution Engine & Tool Calling
- **Description**: Multi-step autonomous agent planner (`agent_planner.py`), stateful task executor (`agent_executor.py`), tool binding (CRM tool, Knowledge tool, Web search tool, Workflow tool).
- **Backend File(s)**: [agent_executor.py](file:///d:/markai/apps/api/src/api/services/agent_executor.py), [agent_planner.py](file:///d:/markai/apps/api/src/api/services/agent_planner.py), [tools/](file:///d:/markai/apps/api/src/api/ai/tools/)
- **Frontend File(s)**: [agents/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/agents/page.tsx)
- **Database Table(s)**: `agents`, `agent_executions`, `agent_tools`
- **API Routes**: `GET /api/v1/agents`, `POST /api/v1/agents`, `POST /api/v1/agents/{id}/execute`
- **Dependencies**: AI Gateway Coordinator
- **Status**: Implemented
- **Tests**: [test_agents.py](file:///d:/markai/apps/api/tests/test_agents.py), [test_tools.py](file:///d:/markai/apps/api/tests/test_tools.py)
- **Owner Module**: `Agents`

---

### 8. Short-Term & Long-Term Memory System
- **Description**: Conversation memory persistence, episodic memory logging, key-value state storage per user/agent.
- **Backend File(s)**: [memory_manager.py](file:///d:/markai/apps/api/src/api/services/memory_manager.py), [memory.py](file:///d:/markai/apps/api/src/api/routes/memory.py)
- **Frontend File(s)**: Integrated with Agent dashboard
- **Database Table(s)**: `memories`, `memory_sessions`
- **API Routes**: `GET /api/v1/memory`, `POST /api/v1/memory`, `DELETE /api/v1/memory/{id}`
- **Dependencies**: SQLAlchemy ORM
- **Status**: Implemented
- **Tests**: Included in Agent integration tests
- **Owner Module**: `Memory`

---

### 9. Knowledge Platform & RAG Document Ingestion
- **Description**: Document uploading, multi-format parsing (PDF, TXT, Markdown, CSV), chunking, vector embedding generation, hybrid semantic search.
- **Backend File(s)**: [rag_engine.py](file:///d:/markai/apps/api/src/api/services/rag_engine.py), [vector_store.py](file:///d:/markai/apps/api/src/api/services/vector_store.py), [document_parser.py](file:///d:/markai/apps/api/src/api/services/document_parser.py)
- **Frontend File(s)**: [knowledge/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/knowledge/page.tsx)
- **Database Table(s)**: `knowledge_bases`, `knowledge_documents`, `knowledge_chunks`
- **API Routes**: `GET /api/v1/ai/knowledge`, `POST /api/v1/ai/knowledge/upload`, `POST /api/v1/ai/knowledge/query`
- **Dependencies**: PyPDF2, docx, numpy / vector utilities
- **Status**: Implemented
- **Tests**: [test_knowledge_platform.py](file:///d:/markai/apps/api/tests/test_knowledge_platform.py)
- **Owner Module**: `Knowledge`

---

### 10. Graph-Based Workflow Automation Engine
- **Description**: Node-based workflow definition, trigger evaluation (Webhook, Schedule, Event), step execution, condition evaluation, and execution run status tracking.
- **Backend File(s)**: [workflow_engine.py](file:///d:/markai/apps/api/src/api/services/workflow_engine.py), [workflows.py](file:///d:/markai/apps/api/src/api/routes/workflows.py)
- **Frontend File(s)**: [workflows/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/workflows/page.tsx)
- **Database Table(s)**: `workflows`, `workflow_nodes`, `workflow_executions`
- **API Routes**: `GET /api/v1/workflows`, `POST /api/v1/workflows`, `POST /api/v1/workflows/{id}/trigger`
- **Dependencies**: SQLAlchemy, asyncio
- **Status**: Implemented
- **Tests**: [test_workflows.py](file:///d:/markai/apps/api/tests/test_workflows.py)
- **Owner Module**: `Workflows`

---

### 11. CRM Core (Leads, Contacts, Companies & Activities)
- **Description**: Full CRM pipeline for managing lead status, customer contacts, company profiles, and sales interaction activities.
- **Backend File(s)**: [crm.py](file:///d:/markai/apps/api/src/api/routes/crm.py)
- **Frontend File(s)**: [crm/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/crm/page.tsx)
- **Database Table(s)**: `leads`, `contacts`, `companies`, `activities`
- **API Routes**: `GET /api/v1/crm/leads`, `POST /api/v1/crm/contacts`, `GET /api/v1/crm/companies`
- **Dependencies**: SQLAlchemy
- **Status**: Implemented
- **Tests**: [test_crm.py](file:///d:/markai/apps/api/tests/test_crm.py)
- **Owner Module**: `CRM`

---

### 12. Marketing Content & Campaign Generator
- **Description**: AI content generator for social media, email campaigns, blog posts, ad copy with multi-variant output generation.
- **Backend File(s)**: [generator.py](file:///d:/markai/apps/api/src/api/routes/generator.py), [campaigns.py](file:///d:/markai/apps/api/src/api/routes/campaigns.py), [campaign.py](file:///d:/markai/apps/api/src/api/services/campaign.py)
- **Frontend File(s)**: [generator/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/generator/page.tsx), [campaigns/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/campaigns/page.tsx)
- **Database Table(s)**: `campaigns`, `content_generators`, `content_variants`
- **API Routes**: `POST /api/v1/generator/generate`, `GET /api/v1/campaigns`
- **Dependencies**: AI Gateway Coordinator
- **Status**: Implemented
- **Tests**: [test_generator.py](file:///d:/markai/apps/api/tests/test_generator.py), [test_campaigns.py](file:///d:/markai/apps/api/tests/test_campaigns.py)
- **Owner Module**: `Campaigns`

---

### 13. Observability, Telemetry & Cost Audit
- **Description**: Real-time request logging, HTTP latency metrics, OpenTelemetry span exporting, Prometheus metric scraping endpoints, cost per token calculation.
- **Backend File(s)**: [observability.py](file:///d:/markai/apps/api/src/api/routes/observability.py), [telemetry.py](file:///d:/markai/apps/api/src/api/core/telemetry.py), [metrics_registry.py](file:///d:/markai/apps/api/src/api/core/metrics_registry.py)
- **Frontend File(s)**: [analytics/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/analytics/page.tsx), [observability.ts](file:///d:/markai/apps/web/src/store/observability.ts)
- **Database Table(s)**: `observability_traces`, `ai_usage_logs`
- **API Routes**: `GET /api/v1/observability/metrics`, `GET /api/v1/observability/logs`
- **Dependencies**: `prometheus_client`, `opentelemetry`
- **Status**: Implemented
- **Tests**: [test_observability.py](file:///d:/markai/apps/api/tests/test_observability.py)
- **Owner Module**: `Observability`

---

### 14. Asynchronous Task Worker System
- **Description**: Celery distributed task queue powered by Redis for background processing (document embedding, bulk email delivery, cleanup jobs).
- **Backend File(s)**: [celery_app.py](file:///d:/markai/apps/api/src/api/worker/celery_app.py)
- **Frontend File(s)**: N/A (Background system)
- **Database Table(s)**: `celery_taskmeta` (managed by Celery result backend)
- **API Routes**: Internal worker queues
- **Dependencies**: `celery`, `redis`
- **Status**: Implemented
- **Tests**: Validated via Async test fixtures
- **Owner Module**: `Worker`
