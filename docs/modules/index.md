# Comprehensive Module Documentation

This document provides detailed operational specifications for every core module in the `markai` application.

---

## 1. Authentication & Security Module (`Auth`)

- **Purpose**: Provides user authentication, JWT token generation, refresh token validation, and password cryptography.
- **Responsibilities**: User login, password hashing, token issuance, active user session verification.
- **Dependencies**: PyJWT, passlib (bcrypt), SQLAlchemy Session.
- **Public APIs**:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/refresh`
  - `GET /api/v1/auth/me`
- **Internal Services**: `api.core.security` (`create_access_token`, `verify_password`, `get_password_hash`)
- **Database Models**: `User`, `Role`, `Permission`, `UserRole`, `RolePermission`
- **Background Jobs**: None
- **Frontend Views**: [login/page.tsx](file:///d:/markai/apps/web/src/app/auth/login/page.tsx), [register/page.tsx](file:///d:/markai/apps/web/src/app/auth/register/page.tsx), `useAuthStore`
- **Testing**: [test_auth.py](file:///d:/markai/apps/api/tests/test_auth.py)
- **Configuration**: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`

---

## 2. Multi-Tenant Organization Module (`Organizations`)

- **Purpose**: Manages multi-tenant organization boundaries, member invitations, tenant settings, and RBAC roles.
- **Responsibilities**: Organization CRUD, user-tenant mapping, tenant role management (`OWNER`, `ADMIN`, `MEMBER`, `GUEST`).
- **Dependencies**: Auth Module, SQLAlchemy.
- **Public APIs**:
  - `GET /api/v1/organizations`
  - `POST /api/v1/organizations`
  - `GET /api/v1/organizations/{id}/members`
  - `POST /api/v1/organizations/{id}/members`
- **Internal Services**: `api.core.deps` (`get_current_org`, `require_permission`)
- **Database Models**: `Organization`, `UserOrganization`
- **Background Jobs**: None
- **Frontend Views**: [settings/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/settings/page.tsx)
- **Testing**: [test_phase2_auth_orgs.py](file:///d:/markai/apps/api/tests/test_phase2_auth_orgs.py)
- **Configuration**: None

---

## 3. AI Gateway 2.0 Module (`AI Gateway`)

- **Purpose**: Orchestrates LLM provider requests, SSE token streaming, provider registry management, and real-time usage logging.
- **Responsibilities**: Multi-provider proxying (OpenAI, Claude, Gemini, Groq, OpenRouter), response formatting, fallback error handling.
- **Dependencies**: `httpx`, `asyncio`, Redis cache.
- **Public APIs**:
  - `POST /api/v1/ai/generate`
  - `POST /api/v1/ai/stream`
  - `GET /api/v1/ai/providers`
  - `GET /api/v1/ai/models`
- **Internal Services**: `AIGatewayCoordinator` ([coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py)), `ProviderRegistry` ([manager.py](file:///d:/markai/apps/api/src/api/ai/registry/manager.py))
- **Database Models**: `AIProvider`, `AIModelRegistry`, `AIUsageLog`
- **Background Jobs**: Sync provider model health checks (`sync_providers_and_models` on startup)
- **Frontend Views**: [ai/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/ai/page.tsx), `useAIStore`
- **Testing**: [test_ai_gateway.py](file:///d:/markai/apps/api/tests/test_ai_gateway.py)
- **Configuration**: Provider API Keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`)

---

## 4. Intelligent Router Module (`AI Router`)

- **Purpose**: Routes AI completion requests based on policy constraints (cost optimization, latency minimization, fallback cascades).
- **Responsibilities**: Evaluating active routing rules, selecting destination model, tracking rule hits.
- **Dependencies**: AI Gateway Module, SQLAlchemy.
- **Public APIs**:
  - `GET /api/v1/ai/routing/rules`
  - `POST /api/v1/ai/routing/rules`
  - `POST /api/v1/ai/routing/resolve`
- **Internal Services**: `AIRouterEngine` ([engine.py](file:///d:/markai/apps/api/src/api/ai/router/engine.py))
- **Database Models**: `AIRoutingRule`
- **Background Jobs**: None
- **Frontend Views**: Integrated into AI Dashboard
- **Testing**: [test_ai_router_phase1b.py](file:///d:/markai/apps/api/tests/test_ai_router_phase1b.py)
- **Configuration**: None

---

## 5. Security & Threat Scanning Module (`Security`)

- **Purpose**: Scans incoming prompt text and outgoing AI completions for security risks, injection attacks, PII exposure, and budget overruns.
- **Responsibilities**: Enforcing pre-execution policies, blocking threat vectors, recording security audit events.
- **Dependencies**: Regex scanners, Pydantic, SQLAlchemy.
- **Public APIs**:
  - `POST /api/v1/security/scan`
  - `GET /api/v1/security/events`
  - `GET /api/v1/security/policies`
- **Internal Services**: `AISecurityPipeline` ([pipeline.py](file:///d:/markai/apps/api/src/api/ai/security/pipeline.py))
- **Database Models**: `SecurityEvent`, `SecurityPolicy`
- **Background Jobs**: None
- **Frontend Views**: [settings/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/settings/page.tsx)
- **Testing**: [test_ai_security_phase1c.py](file:///d:/markai/apps/api/tests/test_ai_security_phase1c.py)
- **Configuration**: None

---

## 6. Prompt Management Module (`Prompts`)

- **Purpose**: Manages reusable prompt templates, version histories, variable schemas, and interactive test runs.
- **Responsibilities**: Template rendering, version control, template execution tracking.
- **Dependencies**: AI Gateway Module.
- **Public APIs**:
  - `GET /api/v1/ai/prompts`
  - `POST /api/v1/ai/prompts`
  - `POST /api/v1/ai/prompts/{id}/execute`
- **Internal Services**: `PromptService` ([prompt.py](file:///d:/markai/apps/api/src/api/services/prompt.py))
- **Database Models**: `Prompt`, `PromptVersion`, `PromptExecution`
- **Background Jobs**: None
- **Frontend Views**: [prompts/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/prompts/page.tsx)
- **Testing**: [test_ai_prompts_extended.py](file:///d:/markai/apps/api/tests/test_ai_prompts_extended.py)
- **Configuration**: None

---

## 7. AI Agent Module (`Agents`)

- **Purpose**: Autonomous agent orchestration engine capable of multi-step planning, state retention, and tool execution.
- **Responsibilities**: Deconstructing goals into action steps (`agent_planner.py`), calling tools (`crm_tool`, `knowledge_tool`, `web_search_tool`, `workflow_tool`), recording step logs (`agent_executor.py`).
- **Dependencies**: AI Gateway, Memory Manager, Tool Registry.
- **Public APIs**:
  - `GET /api/v1/agents`
  - `POST /api/v1/agents`
  - `POST /api/v1/agents/{id}/execute`
- **Internal Services**: `AgentExecutor` ([agent_executor.py](file:///d:/markai/apps/api/src/api/services/agent_executor.py)), `AgentPlanner` ([agent_planner.py](file:///d:/markai/apps/api/src/api/services/agent_planner.py))
- **Database Models**: `Agent`, `AgentExecution`, `AgentTool`
- **Background Jobs**: Async Agent Run Execution via Celery
- **Frontend Views**: [agents/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/agents/page.tsx)
- **Testing**: [test_agents.py](file:///d:/markai/apps/api/tests/test_agents.py)
- **Configuration**: None

---

## 8. Knowledge Platform & RAG Module (`Knowledge`)

- **Purpose**: Ingests unstructured files, chunks text, creates vector embeddings, and performs hybrid RAG searches.
- **Responsibilities**: PDF/DOCX parsing, document vectorization, chunk storage, similarity query resolution.
- **Dependencies**: PyPDF2, docx, `vector_store.py`, `rag_engine.py`.
- **Public APIs**:
  - `GET /api/v1/ai/knowledge`
  - `POST /api/v1/ai/knowledge/upload`
  - `POST /api/v1/ai/knowledge/query`
- **Internal Services**: `RAGEngine` ([rag_engine.py](file:///d:/markai/apps/api/src/api/services/rag_engine.py)), `VectorStoreService` ([vector_store.py](file:///d:/markai/apps/api/src/api/services/vector_store.py)), `DocumentParser` ([document_parser.py](file:///d:/markai/apps/api/src/api/services/document_parser.py))
- **Database Models**: `KnowledgeBase`, `KnowledgeDocument`, `KnowledgeChunk`
- **Background Jobs**: Async document chunking & vector indexing (`process_document_chunking` Celery task)
- **Frontend Views**: [knowledge/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/knowledge/page.tsx)
- **Testing**: [test_knowledge_platform.py](file:///d:/markai/apps/api/tests/test_knowledge_platform.py)
- **Configuration**: `MINIO_ENDPOINT`, `MINIO_BUCKET_NAME`

---

## 9. Workflow Automation Module (`Workflows`)

- **Purpose**: Executes graph-based automation pipelines containing triggers, decision nodes, and action steps.
- **Responsibilities**: Graph traversal, step evaluation, node state updates, retry execution.
- **Dependencies**: SQLAlchemy, Asyncio.
- **Public APIs**:
  - `GET /api/v1/workflows`
  - `POST /api/v1/workflows`
  - `POST /api/v1/workflows/{id}/trigger`
- **Internal Services**: `WorkflowEngine` ([workflow_engine.py](file:///d:/markai/apps/api/src/api/services/workflow_engine.py))
- **Database Models**: `Workflow`, `WorkflowNode`, `WorkflowExecution`
- **Background Jobs**: Workflow Execution Celery Tasks
- **Frontend Views**: [workflows/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/workflows/page.tsx)
- **Testing**: [test_workflows.py](file:///d:/markai/apps/api/tests/test_workflows.py)
- **Configuration**: None

---

## 10. Observability & Telemetry Module (`Observability`)

- **Purpose**: Collects system metrics, trace telemetry, HTTP request logs, and cost analytics across all services.
- **Responsibilities**: Request middleware logging, OpenTelemetry trace export, Prometheus metric registration.
- **Dependencies**: OpenTelemetry, Prometheus Client, Structlog.
- **Public APIs**:
  - `GET /api/v1/observability/metrics`
  - `GET /api/v1/observability/logs`
  - `GET /api/v1/observability/traces`
- **Internal Services**: `api.core.telemetry`, `api.core.metrics_registry`
- **Database Models**: `ObservabilityTrace`, `AIUsageLog`
- **Background Jobs**: Metric rollup background tasks
- **Frontend Views**: [analytics/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/analytics/page.tsx), `useObservabilityStore`
- **Testing**: [test_observability.py](file:///d:/markai/apps/api/tests/test_observability.py)
- **Configuration**: Prometheus / Otel endpoints
