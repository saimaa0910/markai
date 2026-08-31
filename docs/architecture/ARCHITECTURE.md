# EAIMOS Architecture Specification (Frozen Target)

**Document Version**: 1.0.0 — Architecture Freeze  
**Status**: FROZEN  
**Target System**: Enterprise AI Marketing Operating System (EAIMOS / MarkAI)  
**Base Architecture**: Modular Monolith with Domain-Oriented Hexagonal Boundaries  

---

## 1. Architectural Style & Principles

EAIMOS is structured as a **Modular Monolith** organized into distinct, domain-oriented modules with strict hexagonal (ports & adapters) layer boundaries.

```mermaid
graph TD
    subgraph Frontend["Next.js 16 Web App (App Router)"]
        UI["Feature UI & Canvas Builder"]
        ClientService["Centralized API Client / Hooks"]
        AuthStore["Zustand Auth Store"]
    end

    subgraph ReverseProxy["Nginx Reverse Proxy"]
        NginxGateway["Reverse Proxy & Static Asset Gateway"]
    end

    subgraph BackendAPI["FastAPI Modular Monolith"]
        subgraph MiddlewareStack["Middleware Pipeline"]
            Logging["Logging Middleware"]
            Telemetry["Telemetry Middleware"]
            RateLimit["Rate Limit Middleware"]
            CORS["CORS Middleware"]
        end

        subgraph Routes["API Transport Layer (/api/v1)"]
            AuthRoutes["Auth & OAuth Routes"]
            AIRoutes["AI Platform & Gateway Routes"]
            AgentRoutes["Agent Platform Routes"]
            ChatRoutes["Conversations & Chat Routes"]
            StudioRoutes["Image / Social / Content Routes"]
            DomainRoutes["Knowledge / CRM / Campaign / Workflow Routes"]
        end

        subgraph AppServices["Application & Service Layer"]
            AIGateway["Central AI Gateway"]
            AgentRuntime["Generic Agent Runtime"]
            EmailService["Email & Notification Service"]
            DocService["Document Processing Service"]
            TenantService["Tenant & IAM Coordination"]
        end

        subgraph DomainModules["Domain Modules (Entities & Policies)"]
            IAMDomain["IAM & RBAC"]
            AIDomain["AI Policies & Routing"]
            AgentDomain["Agent Manifests & Plans"]
            KnowledgeDomain["Collections & Vectors"]
            WorkflowDomain["Workflow Engines"]
        end

        subgraph InfrastructureLayer["Infrastructure Adapters"]
            Providers["LLM & Image Provider Adapters"]
            SQLAlchemyRepos["Tenant-Scoped Repositories"]
            RedisCache["Redis Cache & Rate Limit"]
            CeleryQueue["Celery Task Queue"]
            S3Storage["MinIO / S3 Storage"]
        end
    end

    subgraph DataPlane["Data & Storage Plane"]
        Postgres["PostgreSQL 16 (Relational + pgvector)"]
        Redis["Redis 7 (Cache, Broker, RateLimit)"]
        MinIO["MinIO / S3 (Assets, Documents)"]
    end

    subgraph WorkerPlane["Asynchronous Workers"]
        CeleryWorker["Celery Worker Daemons"]
        CeleryBeat["Celery Beat Scheduler"]
    end

    UI --> ClientService
    ClientService --> NginxGateway
    NginxGateway --> Routes
    Routes --> MiddlewareStack
    MiddlewareStack --> AppServices
    AppServices --> DomainModules
    AppServices --> InfrastructureLayer
    InfrastructureLayer --> Postgres
    InfrastructureLayer --> Redis
    InfrastructureLayer --> MinIO
    InfrastructureLayer --> CeleryQueue
    CeleryQueue --> CeleryWorker
    CeleryBeat --> CeleryQueue
    CeleryWorker --> Postgres
    CeleryWorker --> MinIO
```

### Core Architecture Invariants:
1. **Single Modular Monolith**: No distributed microservices. All capabilities reside in a single codebase with clean in-process domain boundaries.
2. **Strict Layer Dependency Direction**: Dependencies flow inward from Transport (`routes`) to Application (`services`) to Domain (`models/policies`) to Infrastructure (`repositories/adapters`). No lower layer may import a higher layer.
3. **Single AI Execution Plane**: All AI inferences (Playground, Testing Lab, Compare Lab, Agents, Studios, Chat) must execute through the centralized `AIGateway` and unified provider router. No module may invoke AI providers directly.
4. **Generic Agent Runtime**: `AgentRuntime` coordinates context, planning, tool execution, gateway synthesis, reflection, and evaluation generically. Agent specializations belong in manifests, prompts, and tools—not hardcoded runtime conditionals.
5. **Server-Side Tenant Isolation Invariant**: Multi-tenancy is enforced at the repository and service layers. Every organization-scoped resource requires explicit `organization_id` validation.

---

## 2. Backend Layered Architecture

The backend follows Clean/Hexagonal layered architecture:

```
┌──────────────────────────────────────────────────────────┐
│                      API Transport                       │
│  FastAPI Routers, Request/Response DTOs, Auth Guards     │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   Application Services                   │
│  Use Case Orchestration, Workflows, Gateway Coordination │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                      Domain Layer                        │
│  Entities, Aggregates, Value Objects, Domain Policies    │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   Repositories & Ports                   │
│  Tenant-Scoped Data Access Interfaces, Abstractions      │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                    │
│  SQLAlchemy ORM, Postgres/pgvector, Redis, MinIO, Celery │
└──────────────────────────────────────────────────────────┘
```

### Layer Responsibilities:

| Layer | Directory Location | Permitted Responsibilities | Prohibited Actions |
|---|---|---|---|
| **API Transport** | `apps/api/src/api/routes/` | HTTP request routing, input validation via Pydantic schemas, dependency injection (`Depends`), HTTP status codes, SSE streaming response envelopes. | No direct business calculations, no direct external API calls, no bypassing services. |
| **Application Services** | `apps/api/src/api/services/`, `apps/api/src/api/ai/` | Orchestrating use cases, invoking repositories, managing transactional units, dispatching background tasks, coordinating AI gateway. | No direct HTTP request parsing, no raw SQL string execution. |
| **Domain Layer** | `apps/api/src/api/models/` | SQLAlchemy entity definitions, table relationships, domain enums, status transitions, schema constraints. | No dependency on routes or external HTTP clients. |
| **Repositories / Ports** | `apps/api/src/api/repositories/` | Tenant-scoped data persistence operations, query filtering, pagination helpers, soft-delete filtering. | No global unbound database queries without tenant isolation. |
| **Infrastructure** | `apps/api/src/api/ai/providers/`, `api/worker/`, `api/database/` | Postgres connection management, pgvector operations, Redis caching, Celery task definitions, MinIO/S3 SDK integration, external provider REST adapters. | No coupling to transport-specific schemas. |

---

## 3. Shared Core & Cross-Cutting Infrastructure

The shared core (`apps/api/src/api/core/`) is kept minimal and strictly cross-cutting:

- **Configuration** (`api.core.config`): Pydantic Settings resolving environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`, `MINIO_ENDPOINT`, `CORS_ORIGINS`).
- **Security Primitives** (`api.core.security`): Cryptographic JWT encode/decode, bcrypt password hashing, Fernet provider credential encryption.
- **Dependencies & Context** (`api.core.deps`): `get_db`, `get_current_user`, `get_tenant_context`, `RoleChecker`.
- **Telemetry & Tracing** (`api.core.telemetry`): OpenTelemetry tracer initializers and distributed trace span context managers.
- **Database Session** (`api.database.session`): Engine connection pooling (`pool_size=50`, `max_overflow=100`, `pool_pre_ping=True`).

---

## 4. Multi-Tenant Architecture & Data Isolation

Multi-tenancy in EAIMOS is a platform-level invariant enforced server-side.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Route as FastAPI Router
    participant Guard as Auth & Tenant Guard
    participant Service as Application Service
    participant Repo as Tenant Repository
    participant DB as PostgreSQL

    User->>Route: HTTP Request + Bearer JWT + X-Organization-ID
    Route->>Guard: Validate JWT & Tenant Membership
    Guard-->>Route: User + UserOrganization (Validated Tenant Context)
    Route->>Service: execute_use_case(tenant_id, user_id, payload)
    Service->>Repo: find_by_id_and_org(resource_id, tenant_id)
    Repo->>DB: SELECT ... WHERE id = :id AND organization_id = :tenant_id AND deleted_at IS NULL
    DB-->>Repo: Record
    Repo-->>Service: Entity
    Service-->>Route: Result
    Route-->>User: JSON Response Envelope
```

### Invariants:
1. Every organization-owned entity possesses a non-nullable `organization_id: UUID` foreign key pointing to `organizations.id`.
2. Every database read, update, and delete query must include `organization_id == active_tenant_id`.
3. Switching organizations requires a valid `UserOrganization` membership record in the target organization.
4. Quotas and token usage limits (`AIOrgLimit`) are scoped to the active tenant.

---

## 5. Central IAM & Authorization Architecture

### Triad Model:
- **Authentication** (*Who are you?*): Validated via JWT access tokens and database session tracking.
- **Authorization** (*What can you do?*): Verified via `RoleChecker` evaluating `UserRole` and granular `Permission` records.
- **Tenant Context** (*Where are you operating?*): Resolved via `UserOrganization` linking `user_id` and `organization_id`.

```mermaid
graph LR
    subgraph Auth["Authentication Engine"]
        Credentials["User Credentials / OAuth"] --> JWT["Signed JWT Access Token"]
        JWT --> SessionTracker["UserSession DB Tracking"]
        Refresh["Refresh Token"] --> TokenFamily["Family Reuse Revocation"]
        MFA["TOTP MFA"] --> BackupCodes["Hashed Single-Use Codes"]
    end

    subgraph RBAC["Authorization Engine"]
        UserOrg["UserOrganization"] --> RoleEnum["UserRole (OWNER, ADMIN, MEMBER, GUEST)"]
        UserOrg --> CustomRole["Custom Role Assignment"]
        CustomRole --> Permissions["Granular Permissions Matrix"]
    end

    subgraph Audit["Compliance Engine"]
        Actions["Mutating API Actions"] --> AuditLog["Immutable audit_logs Table"]
    end
```

---

## 6. AI Platform Architecture

The centralized AI Platform executes all model interactions across text, image, audio, video, vision, embeddings, and multimodal capabilities.

```mermaid
graph TD
    Client["Playground / Testing Lab / Compare Lab / Agent Runtime / Studios"]
    Client --> AIGateway["Central AIGateway Coordinator"]
    
    subgraph SecurityPipeline["Pre-Execution Security Pipeline"]
        AIGateway --> InjectionCheck["Prompt Injection Scanner"]
        InjectionCheck --> ToxicCheck["Toxic Content Filter"]
        ToxicCheck --> PIIScanner["PII Redactor / Anonymizer"]
    end

    subgraph RoutingEngine["Provider Router & Circuit Breaker"]
        PIIScanner --> CircuitBreaker["Circuit Breaker (5 Failure Threshold)"]
        CircuitBreaker --> FallbackChain["Sequential Failover Resolver"]
        FallbackChain --> DecryptKey["Dynamic Fernet Key Decryption"]
    end

    subgraph ProviderRegistry["Unified Provider Registry"]
        DecryptKey --> Adapter["Provider Adapter Contract"]
        Adapter --> OpenAI["OpenAI Adapter"]
        Adapter --> Claude["Claude Adapter"]
        Adapter --> Gemini["Gemini Adapter"]
        Adapter --> Groq["Groq Adapter"]
        Adapter --> ImageAdapters["Pollinations / DALL-E / Imagen / Stability / Fal / Replicate"]
    end

    subgraph TelemetrySink["Post-Execution Telemetry & Cost Engine"]
        OpenAI --> CostCalc["Token Cost Calculator"]
        Claude --> CostCalc
        Gemini --> CostCalc
        Groq --> CostCalc
        ImageAdapters --> CostCalc
        CostCalc --> DBUsage["AITokenUsage Record"]
        CostCalc --> Prometheus["Prometheus Metrics"]
        CostCalc --> OTel["OpenTelemetry Distributed Spans"]
    end
```

---

## 7. Generic Agent Platform Architecture

The Agent Platform decouples agent logic from specific domains, executing all agent tasks through a uniform lifecycle.

```mermaid
graph TD
    Start["User Prompt / Session Input"] --> BuildCtx["ContextBuilder: System Prompt + RAG + Brand Voice + History"]
    BuildCtx --> PlanGen["AgentPlannerService: JSON Execution Plan"]
    PlanGen --> ToolExec["ToolExecutor: Sandboxed Tool Invocations"]
    
    subgraph ToolSandbox["Sandboxed Tool Registry"]
        ToolExec --> ToolKnowledge["knowledge_tool (RAG pgvector)"]
        ToolExec --> ToolCalendar["calendar_tool (Marketing Schedules)"]
        ToolExec --> ToolSEO["seo_tool (Keyword Analytics)"]
        ToolExec --> ToolWeb["web_search_tool (External Research)"]
    end

    ToolSandbox --> GatewayCall["AIGateway: Synthesize Final Output"]
    GatewayCall --> Reflector["AIReflector: Quality & Hallucination Check"]
    Reflector --> Evaluator["AIEvaluator: Grade Run & agent_evaluations"]
    Evaluator --> Memory["MemoryManager: Persist Semantic Memory"]
    Memory --> Complete["AgentRun Result (COMPLETED)"]
```

---

## 8. Data & Storage Architecture

### PostgreSQL 16 & pgvector:
- Primary transactional store for all relational entities.
- Semantic vector embeddings stored in `knowledge_document_chunks.embedding` using `vector(1536)` with cosine distance (`<=>`) HNSW/IVFFlat indexing.

### Redis 7:
- Session cache and fast quota usage counters.
- Token-bucket rate limiting backend (`RateLimitMiddleware`).
- Message broker and result backend for Celery background tasks.

### MinIO / S3:
- Object storage bucket `eaimos-storage` for generated images, uploaded documents, knowledge PDFs, and CSV exports.

---

## 9. Asynchronous Processing Architecture

```mermaid
graph LR
    API["FastAPI API Request"] --> CeleryApp["Celery Broker (Redis)"]
    Beat["Celery Beat Scheduler"] --> CeleryApp
    
    subgraph CeleryWorkers["Celery Worker Tasks"]
        CeleryApp --> TaskDoc["process_document_pipeline_task"]
        CeleryApp --> TaskImg["generate_image_task"]
        CeleryApp --> TaskEmail["send_email_task"]
        CeleryApp --> TaskAgent["agent_run_task"]
        CeleryApp --> TaskPurge["purge_deleted_accounts_task"]
        CeleryApp --> TaskQuota["quota_reset_worker_task"]
        CeleryApp --> TaskHealth["health_worker_task"]
    end

    TaskDoc --> PG["PostgreSQL"]
    TaskImg --> MinIO["MinIO Storage"]
    TaskEmail --> Resend["Resend / SMTP"]
```

---

## 10. Frontend Architecture (Next.js 16)

The frontend adopts a **Feature-Based Architecture**:

```
apps/web/src/
├── app/                         # Next.js App Router pages & layouts
│   ├── (marketing)/             # Public marketing & documentation pages
│   ├── auth/                    # Authentication flows
│   └── dashboard/               # Protected workspace dashboard
├── features/                    # Feature modules (Components, Hooks, Store, API)
│   ├── ai-platform/             # Observability, Playground, Compare, Models, Router
│   ├── agents/                  # Agent builder, marketplace, runs, playground
│   ├── image-studio/            # Image canvas, generation, inpainting, history
│   ├── social/                  # Multi-platform post creator, scheduler, calendar
│   ├── content-studio/          # Long-form article & copywriting studio
│   ├── knowledge/               # Knowledge base, collections, document parser
│   ├── campaigns/               # Marketing campaigns & broadcast builder
│   ├── crm/                     # Contacts, segments, lead management
│   ├── prompts/                 # Prompt library, template editor, testing lab
│   └── workflows/               # Drag-and-drop automation flow builder
├── components/ui/               # Reusable atomic UI components
├── services/                    # Centralized Axios API client (api-client.ts)
├── store/                       # Global Zustand stores (auth.ts, theme.ts)
└── platform/                    # Cross-cutting error sanitizers and utilities
```

---

## 11. Security, Observability & Quality Gates

1. **Error Sanitization Contract**:
   - Backend returns structured error JSON: `{"detail": "Machine readable message", "code": "ERROR_CODE"}`.
   - Frontend passes errors through `getSafeErrorMessage()` to prevent leakage of stack traces, SQL errors, or file paths.
2. **Telemetry & Observability**:
   - OpenTelemetry spans wrapping all HTTP requests and Celery tasks.
   - Prometheus metrics exposed on `/metrics`.
   - `AlertEngine` automatically reporting system incidents upon background job failures.
3. **Quality Gates**:
   - Every commit must pass architecture fitness rules, type checks, lint checks, unit tests, and migration validation.
