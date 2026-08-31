# Domain Boundaries & Bounded Contexts

**System**: Enterprise AI Marketing Operating System (EAIMOS / MarkAI)  
**Status**: APPROVED & FROZEN  
**Date**: August 31, 2026  

---

## 1. Domain Bounded Contexts Overview

EAIMOS is organized into **15 Bounded Contexts**. Each context possesses strict ownership over its database models, application services, and business rules.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Core Platform Contexts                            │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │          IAM          │  │     Organizations     │  │  Notifications  │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                          AI & Intelligence Engine                           │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │      AI Platform      │  │    Agent Platform     │  │ Knowledge / RAG │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Creative & Studio Layer                           │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │     Image Studio      │  │     Social Studio     │  │ Content Studio  │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                         Productivity & Workspaces                           │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │     Conversations     │  │   Prompts Platform    │  │  Files & Assets │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Marketing & Automation                            │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │       Campaigns       │  │          CRM          │  │    Workflows    │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Bounded Context Specifications

### 1. IAM Context (Identity & Access Management)
- **Purpose**: User identity, credential authentication, MFA, OAuth, session management, RBAC, and security audit logs.
- **Owned Models**: `User`, `UserSession`, `RefreshToken`, `Role`, `Permission`, `RolePermission`, `UserRole`, `AuditLog`.
- **Inbound Interfaces**: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/mfa/*`, `POST /oauth/*`, `GET/POST /rbac/*`, `GET/PATCH /users/*`.
- **Outbound Dependencies**: `api.core.security`, `api.services.email_service` (for verification/reset emails).
- **Forbidden Actions**: Must not query business domains (e.g. `Campaigns`, `CRM`, `Knowledge`) directly.
- **Database Tables**: `users`, `user_sessions`, `refresh_tokens`, `roles`, `permissions`, `role_permissions`, `user_roles`, `audit_logs`.

---

### 2. Organizations Context
- **Purpose**: Tenant creation, multi-tenant boundaries, workspace membership, team invitations, and tenant quotas.
- **Owned Models**: `Organization`, `UserOrganization`, `Invitation`, `OrganizationSettings`.
- **Inbound Interfaces**: `GET/POST /organizations/*`, `POST /invitations/*`, `GET /memberships/*`.
- **Outbound Dependencies**: `IAM Context`, `api.services.email_service`.
- **Forbidden Actions**: Must not access AI provider execution logic directly.
- **Database Tables**: `organizations`, `user_organizations`, `invitations`, `organization_settings`.

---

### 3. AI Platform Context
- **Purpose**: Centralized AI model orchestration, LLM/Image provider adapters, circuit breakers, fallback routing, prompt security scanning, token accounting, and cost tracking.
- **Owned Models**: `AIProvider`, `AIProviderKey`, `AIModel`, `AIModelRegistry`, `AITokenUsage`, `AIOrgLimit`, `AIRoutingPolicy`, `AISecurityPolicyRule`, `AIProviderHealth`.
- **Inbound Interfaces**: `AIGateway.chat()`, `AIGateway.stream()`, `POST /ai/playground/*`, `POST /ai/compare/*`, `GET/PUT /ai/models/*`, `GET/PUT /ai/router/*`, `GET /ai/analytics/*`.
- **Outbound Dependencies**: `api.core.config` (encryption key), external AI Provider REST APIs.
- **Forbidden Actions**: Must not store end-user domain assets (e.g. documents, CRM leads).
- **Database Tables**: `ai_providers`, `ai_provider_keys`, `ai_models`, `ai_model_registries`, `ai_token_usages`, `ai_org_limits`, `ai_routing_policies`, `ai_security_policy_rules`, `ai_provider_health`.

---

### 4. Conversations Context
- **Purpose**: Multi-turn chat sessions, message streaming, thread management, bookmarks, shares, and participant collaboration.
- **Owned Models**: `Conversation`, `Message`, `ChatAttachment`, `ChatParticipant`, `ConversationBookmark`, `ConversationShare`.
- **Inbound Interfaces**: `GET/POST /chat/conversations/*`, `POST /chat/conversations/{id}/stream`.
- **Outbound Dependencies**: `AI Platform Context` (`AIGateway`), `Files Context`.
- **Forbidden Actions**: Must not call external AI APIs directly without going through `AIGateway`.
- **Database Tables**: `conversations`, `messages`, `chat_attachments`, `chat_participants`, `conversation_bookmarks`, `conversation_shares`.

---

### 5. Prompts Platform Context
- **Purpose**: System and user prompt template authoring, variable parameterization, version history, testing lab sandboxing, and sharing.
- **Owned Models**: `Prompt`, `PromptVersion`.
- **Inbound Interfaces**: `GET/POST /ai/prompts/*`, `POST /ai/prompts/test/stream`.
- **Outbound Dependencies**: `AI Platform Context` (`AIGateway`).
- **Forbidden Actions**: Must not implement independent AI execution logic.
- **Database Tables**: `prompts`, `prompt_versions`.

---

### 6. Agent Platform Context
- **Purpose**: Autonomous agent definitions, capabilities, planning, tool execution, reflection, evaluation, and semantic memory.
- **Owned Models**: `AgentDefinition`, `AgentSession`, `AgentRun`, `AgentLog`, `AgentMemory`, `AgentEvaluation`.
- **Inbound Interfaces**: `GET/POST /agents/definitions/*`, `POST /agents/sessions/*`, `POST /agents/{id}/chat`, `POST /agents/{id}/stream`.
- **Outbound Dependencies**: `AI Platform Context` (`AIGateway`), `Knowledge Context` (`knowledge_tool`), `Campaigns Context` (`calendar_tool`).
- **Forbidden Actions**: Runtime must not branch on specific agent types using hardcoded conditionals.
- **Database Tables**: `agent_definitions`, `agent_sessions`, `agent_runs`, `agent_logs`, `agent_memories`, `agent_evaluations`.

---

### 7. Image Studio Context
- **Purpose**: Visual creative generation, prompt engineering, aspect ratio optimization, inpainting, variations, upscaling, and creative asset history.
- **Owned Models**: `AIImageLibrary`, `AIImageVariation`.
- **Inbound Interfaces**: `POST /agents/image/generate`, `POST /agents/image/edit`, `POST /agents/image/upscale`, `GET /agents/image/history`.
- **Outbound Dependencies**: `AI Platform Context` (`ImageProviderRouter`), `Files Context` (`AssetManager`).
- **Forbidden Actions**: Must not bypass `ImageProviderRouter` to make ad-hoc provider calls.
- **Database Tables**: `ai_image_library`, `ai_image_variations`.

---

### 8. Social Studio Context
- **Purpose**: Multi-platform social copy generation, hashtag optimization, character limit validation, and publishing to social networks.
- **Owned Models**: Integrated into `AgentRun` and `AIBackgroundJob`.
- **Inbound Interfaces**: `POST /agents/social/generate`, `POST /agents/social/publish`, `POST /agents/social/schedule`.
- **Outbound Dependencies**: `AI Platform Context` (`AIGateway`), `Image Studio Context`, external social platform APIs (LinkedIn, Twitter, Facebook).
- **Forbidden Actions**: Must not execute LLM completions without `AIGateway`.
- **Database Tables**: Shares `agent_runs`, `agent_logs`, `ai_background_jobs`.

---

### 9. Content Studio Context
- **Purpose**: Long-form blog posts, email copy, product descriptions, SEO articles, and brand voice alignment.
- **Owned Models**: Integrated into `AgentRun` and `Campaign`.
- **Inbound Interfaces**: `POST /agents/content/generate`, `POST /agents/content/stream`.
- **Outbound Dependencies**: `AI Platform Context` (`AIGateway`), `Knowledge Context`.
- **Forbidden Actions**: Must not bypass the generic `AgentRuntime`.
- **Database Tables**: Shares `agent_runs`, `agent_logs`.

---

### 10. Knowledge & RAG Context
- **Purpose**: Document upload, vector chunking, pgvector embedding generation, semantic similarity search, and collection management.
- **Owned Models**: `KnowledgeCollection`, `KnowledgeFolder`, `KnowledgeDocument`, `KnowledgeDocumentChunk`, `KnowledgeProcessingJob`.
- **Inbound Interfaces**: `GET/POST /knowledge/collections/*`, `POST /knowledge/documents/*`, `POST /knowledge/search`.
- **Outbound Dependencies**: `AI Platform Context` (Embeddings capability), `Files Context`.
- **Forbidden Actions**: Must not query other tenants' document chunks.
- **Database Tables**: `knowledge_collections`, `knowledge_folders`, `knowledge_documents`, `knowledge_document_chunks`, `knowledge_processing_jobs`.

---

### 11. Campaigns Context
- **Purpose**: Marketing campaigns, newsletter scheduling, broadcast execution, and conversion metrics.
- **Owned Models**: `Campaign`, `CampaignActivity`.
- **Inbound Interfaces**: `GET/POST /campaigns/*`, `POST /campaigns/{id}/broadcast`.
- **Outbound Dependencies**: `CRM Context`, `Notifications Context` (`EmailService`), `Celery Workers`.
- **Forbidden Actions**: Must not perform bulk email dispatch synchronously in the HTTP thread.
- **Database Tables**: `campaigns`, `campaign_activities`.

---

### 12. CRM Context
- **Purpose**: Contact lead management, audience segmentation, lifecycle stages, and customer activity logs.
- **Owned Models**: `Contact`, `ContactSegment`, `ContactActivity`.
- **Inbound Interfaces**: `GET/POST /crm/contacts/*`, `GET/POST /crm/segments/*`.
- **Outbound Dependencies**: `Organizations Context`.
- **Forbidden Actions**: Must not leak contacts across organizations.
- **Database Tables**: `contacts`, `contact_segments`, `contact_activities`.

---

### 13. Workflows Context
- **Purpose**: Visual DAG-based workflow builder, step execution engine, trigger listening, and execution logs.
- **Owned Models**: `WorkflowDefinition`, `WorkflowExecution`, `WorkflowStep`, `WorkflowStepExecution`.
- **Inbound Interfaces**: `GET/POST /workflows/*`, `POST /workflows/{id}/execute`.
- **Outbound Dependencies**: `Agent Platform Context`, `Campaigns Context`, `CRM Context`.
- **Forbidden Actions**: Workflow step loops must be bounded to prevent infinite recursion.
- **Database Tables**: `workflow_definitions`, `workflow_executions`, `workflow_steps`, `workflow_step_executions`.

---

### 14. Files & Assets Context
- **Purpose**: Upload handling, MIME type verification, file asset tracking, download streaming, and MinIO/S3 object storage interface.
- **Owned Models**: `FileAsset`.
- **Inbound Interfaces**: `POST /files/upload`, `GET /files/{id}/download`, `DELETE /files/{id}`.
- **Outbound Dependencies**: MinIO / S3 SDK.
- **Forbidden Actions**: Must not allow unrestricted file path traversal.
- **Database Tables**: `file_assets`.

---

### 15. Notifications & Email Context
- **Purpose**: Transactional emails, in-app notifications, Resend/SMTP delivery, Celery background queueing, and email delivery audit logs.
- **Owned Models**: `Notification`, `EmailLog`.
- **Inbound Interfaces**: `POST /notifications/*`, `EmailService.send_email()`.
- **Outbound Dependencies**: Resend REST API, SMTP Server, Celery Task Broker.
- **Forbidden Actions**: Must not send emails without logging delivery status to `email_logs`.
- **Database Tables**: `notifications`, `email_logs`.
