# API Endpoint Reference

## Overview

All API endpoints are prefixed with `/api/v1` (configured via `settings.API_V1_STR`). Authentication is performed via standard HTTP Authorization Bearer headers (`Authorization: Bearer <JWT_ACCESS_TOKEN>`).

---

## Endpoint Catalog

### 1. Authentication (`/api/v1/auth`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Login user & issue JWT access/refresh tokens | No | `UserLoginSchema` | `TokenSchema` | [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L30) |
| `POST` | `/auth/register` | Register new user & seed initial organization | No | `UserCreateSchema` | `UserResponseSchema` | [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L65) |
| `POST` | `/auth/refresh` | Rotate expired access token using valid refresh token | No | `RefreshTokenSchema` | `TokenSchema` | [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L110) |
| `GET` | `/auth/me` | Retrieve currently authenticated user profile | Yes | None | `UserResponseSchema` | [auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L140) |

---

### 2. Organizations & RBAC (`/api/v1/organizations`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/organizations` | List organizations user belongs to | Yes | None | `List[OrganizationResponse]` | [organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py#L25) |
| `POST` | `/organizations` | Create new organization tenant | Yes | `OrganizationCreate` | `OrganizationResponse` | [organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py#L50) |
| `GET` | `/organizations/{id}/members` | List organization members & RBAC roles | Yes | None | `List[MemberResponse]` | [organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py#L85) |
| `POST` | `/organizations/{id}/members` | Invite new member to organization | Yes (`manage_users`) | `MemberInviteSchema` | `MemberResponse` | [organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py#L120) |

---

### 3. AI Gateway & Multi-Provider Completion (`/api/v1/ai`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/ai/generate` | Synchronous multi-provider LLM text completion | Yes | `AIGenerateRequest` | `AIGenerateResponse` | [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L120) |
| `POST` | `/ai/stream` | Real-time SSE token streaming LLM completion | Yes | `AIGenerateRequest` | `EventSourceResponse` | [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L180) |
| `GET` | `/ai/providers` | List registered AI providers & health status | Yes | None | `List[AIProviderSchema]` | [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L40) |
| `GET` | `/ai/models` | List active models in AI Model Registry | Yes | None | `List[AIModelSchema]` | [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L75) |
| `POST` | `/ai/playground/run` | Execute interactive prompt test in Playground | Yes | `PlaygroundRunRequest` | `PlaygroundRunResponse` | [ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L310) |

---

### 4. AI Agents & Execution (`/api/v1/agents`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/agents` | List created AI agents | Yes | None | `List[AgentResponse]` | [agents.py](file:///d:/markai/apps/api/src/api/routes/agents.py#L30) |
| `POST` | `/agents` | Create new autonomous agent definition | Yes | `AgentCreateSchema` | `AgentResponse` | [agents.py](file:///d:/markai/apps/api/src/api/routes/agents.py#L70) |
| `POST` | `/agents/{id}/execute` | Trigger execution run for an agent with goal input | Yes | `AgentExecuteSchema` | `AgentExecutionResponse` | [agents.py](file:///d:/markai/apps/api/src/api/routes/agents.py#L140) |

---

### 5. Knowledge & RAG Platform (`/api/v1/ai/knowledge`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/ai/knowledge` | List knowledge bases for organization | Yes | None | `List[KnowledgeBaseResponse]` | [knowledge.py](file:///d:/markai/apps/api/src/api/routes/knowledge.py#L40) |
| `POST` | `/ai/knowledge/upload` | Upload & ingest document into Knowledge Base | Yes | `UploadFile` (Multipart) | `KnowledgeDocResponse` | [knowledge.py](file:///d:/markai/apps/api/src/api/routes/knowledge.py#L110) |
| `POST` | `/ai/knowledge/query` | Execute hybrid RAG semantic vector search query | Yes | `RAGQueryRequest` | `RAGQueryResponse` | [knowledge.py](file:///d:/markai/apps/api/src/api/routes/knowledge.py#L220) |

---

### 6. Workflow Automation (`/api/v1/workflows`)

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/workflows` | List workflow pipelines | Yes | None | `List[WorkflowResponse]` | [workflows.py](file:///d:/markai/apps/api/src/api/routes/workflows.py#L25) |
| `POST` | `/workflows` | Create node-graph workflow definition | Yes | `WorkflowCreateSchema` | `WorkflowResponse` | [workflows.py](file:///d:/markai/apps/api/src/api/routes/workflows.py#L60) |
| `POST` | `/workflows/{id}/trigger` | Trigger execution run of workflow | Yes | `WorkflowTriggerSchema` | `WorkflowExecutionResponse` | [workflows.py](file:///d:/markai/apps/api/src/api/routes/workflows.py#L130) |

---

### 7. Observability & System Health

| Method | Route | Purpose | Auth Required | Request Model | Response Model | Source File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Root system health check | No | None | `{"status": "healthy"}` | [main.py](file:///d:/markai/apps/api/src/api/main.py#L193) |
| `GET` | `/ready` | Readiness check verifying DB, Redis, MinIO & AI | No | None | Readiness JSON | [main.py](file:///d:/markai/apps/api/src/api/main.py#L222) |
| `GET` | `/api/v1/observability/metrics` | Return Prometheus telemetry metrics | Yes | None | Prometheus Text / JSON | [observability.py](file:///d:/markai/apps/api/src/api/routes/observability.py#L35) |
| `GET` | `/api/v1/observability/logs` | Fetch system execution logs | Yes | None | `List[LogEntrySchema]` | [observability.py](file:///d:/markai/apps/api/src/api/routes/observability.py#L80) |
