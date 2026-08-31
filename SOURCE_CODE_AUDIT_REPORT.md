# EAIMOS / MarkAI — Master Source-Code Audit Report

**Audit Date**: August 31, 2026  
**Auditor**: Antigravity Source-Code Auditor  
**Audit Target**: `d:\markai` repository (FastAPI backend, Next.js frontend, Monorepo packages, Infrastructure, Migrations, Test Suites)  
**Source of Truth**: Active executable source code, migrations, configurations, Dockerfiles, and runtime logic only.

---

## 1. Executive Summary

This master audit evaluated the **Enterprise AI Marketing Operating System (EAIMOS / MarkAI)** repository exclusively through static and dynamic analysis of actual source code, database migration graphs, dependency manifests, runtime controllers, and test suites. 

### Key Findings Summary:
1. **Core Runtime Engine is Real & Production-Grade**:
   - The centralized AI Gateway (`apps/api/src/api/ai/gateway/coordinator.py`), text provider adapters (`openai.py`, `claude.py`, `gemini.py`, `groq.py`, `ollama.py`), and image provider adapters (`pollinations.py`, `openai_images.py`, `google_imagen.py`, `stability.py`, `replicate.py`, `fal.py`, `ideogram.py`, `blackforestlabs.py`) are fully implemented with real HTTP integrations via `httpx` and `requests`. Circuit breaking, failover routing, token cost calculation, Prometheus metric logging, OpenTelemetry spans, and security scanning (PII, injection, toxic content) are actively functional.
   - The Authentication subsystem (`apps/api/src/api/routes/auth.py`) implements bcrypt password hashing, JWT generation, cryptographic Refresh Token Family rotation with automatic reuse revocation, TOTP MFA with backup codes, account lockout after 5 consecutive failures, and soft-delete account reactivation.
   - The Database layer possesses 40 Alembic migration revisions in a single, unbroken linear chain (`84fd17436689` → `9a1b2c3d4e5f`), integrating `pgvector` for semantic vector similarity search.
   - Celery background workers and Celery Beat scheduler (`apps/api/src/api/worker/celery_app.py`) handle asynchronous tasks for document ingestion, email delivery (Resend REST API + SMTP fallback), image generation, daily quota reset, provider health checks, and scheduled account purging.

2. **Severe Architectural Disconnects & Dead Code**:
   - **Stub Monorepo Packages**: `packages/api-client`, `packages/database`, `packages/observability`, and `packages/sdk` are 10-to-19-line mock stubs with `// TODO` comments and hardcoded responses. The Next.js frontend and FastAPI backend do not consume them; the frontend instead uses its own internal Axios client (`apps/web/src/services/api-client.ts`).
   - **Unused Domain Layer**: `apps/api/src/api/domain/` contains 167 skeleton Python files (`return None`) created during DDD prototyping that are never imported by the live FastAPI application or routers.
   - **Service Layer Duplication & Bypassing**: Full domain services in `apps/api/src/api/services/iam/role_service.py` and similar subdirectories are orphaned and completely bypassed by active HTTP routes in `apps/api/src/api/routes/`, which perform direct SQLAlchemy queries.
   - **Model Symbol Clashing**: `UserRole` enum in `api/models/membership.py` (`OWNER`, `ADMIN`, `MEMBER`, `GUEST`) collides with `UserRole` table model in `api/models/iam.py` (`user_roles`). In `api/models/__init__.py`, the IAM table model clobbers the Enum in `__all__`.
   - **Endpoint Duplication**: Session management is implemented three times across `routes/auth.py`, `routes/auth_session.py`, and `routes/sessions.py`. Audit logging is implemented twice across `routes/audit.py` and `routes/audit_logs.py`. Prompts are implemented twice across `routes/prompts.py` and `routes/ai.py`.
   - **Frontend Middleware Execution Gap**: The Next.js route guard is located in `apps/web/src/proxy.ts` exporting `function proxy(...)` instead of `apps/web/src/middleware.ts` exporting `function middleware(...)`, meaning Next.js does not execute the server-side route guard at runtime.
   - **Mock Usages in Analytics Route**: `GET /api/v1/ai/analytics` runs `seed_dummy_usages()`, inserting 120 fake mock token usage records into the database for any organization with zero recorded usage.

---

## 2. Repository Architecture

```
d:\markai\
├── apps/
│   ├── api/                     # FastAPI backend (Python 3.13, SQLAlchemy, Alembic, Celery)
│   └── web/                     # Next.js 16 App Router frontend (React 19, Tailwind v4, Zustand)
├── packages/                    # Monorepo packages (largely stubs)
│   ├── api-client/              # Stub isomorphic API client
│   ├── config/                  # ESLint and TypeScript configs
│   ├── database/                # Stub database package
│   ├── feature-flags/           # Feature flag utility
│   ├── logger/                  # Logger package
│   ├── observability/           # Stub OpenTelemetry package
│   ├── sdk/                     # Stub EAIMOS SDK
│   ├── shared/                  # Shared TypeScript helpers
│   ├── types/                   # Core shared TypeScript types
│   └── ui/                      # Basic React component package (@eaimos/ui)
├── infra/                       # Infrastructure configs
│   ├── docker/                  # Dockerfiles for API, Web, Postgres (pgvector), Nginx, Otel, Prometheus
│   └── scripts/                 # Maintenance shell scripts
├── ai/                          # Top-level dead stub directory (index.ts)
├── services/                    # Top-level dead stub directory (index.ts)
├── tools/                       # Top-level CLI stub (cli.ts)
├── templates/                   # Marketing prompt templates
├── examples/                    # Integration examples
└── docker-compose.yml           # Complete 13-service orchestration stack
```

### Component Code Evidence:
- `FILE`: [packages/api-client/src/index.ts](file:///d:/markai/packages/api-client/src/index.ts#L1-L19)  
  `FUNCTION/CLASS`: `ApiClient`  
  `CURRENT BEHAVIOR`: 19-line stub returning `{}` with `// TODO: Perform fetch GET call`.  
  `EXPECTED BEHAVIOR`: Fully typed SDK client for EAIMOS REST API.  
  `STATUS`: 🔵 `MOCK/STUB`  
  `SEVERITY`: `HIGH`

- `FILE`: [packages/database/src/index.ts](file:///d:/markai/packages/database/src/index.ts#L1-L19)  
  `FUNCTION/CLASS`: `DatabaseClient`  
  `CURRENT BEHAVIOR`: 19-line stub with `// TODO: Connect to Postgres`.  
  `EXPECTED BEHAVIOR`: TypeScript ORM / Prisma / Kysely client if used across packages, or removed if backend is purely Python.  
  `STATUS`: ⚫ `MISSING`  
  `SEVERITY`: `LOW`

- `FILE`: [packages/sdk/src/index.ts](file:///d:/markai/packages/sdk/src/index.ts#L1-L19)  
  `FUNCTION/CLASS`: `EaimosClient`  
  `CURRENT BEHAVIOR`: Returns hardcoded `{ status: 'healthy' }`.  
  `EXPECTED BEHAVIOR`: Public client SDK for Node.js / Browser developers.  
  `STATUS`: 🔵 `MOCK/STUB`  
  `SEVERITY`: `HIGH`

---

## 3. Backend Architecture

### Application Setup & Middleware Stack
Entry point: [apps/api/src/api/main.py](file:///d:/markai/apps/api/src/api/main.py#L1-L327)

```
HTTP Request
     │
     ▼
LoggingMiddleware (Correlation ID, structlog request logging)
     │
     ▼
TelemetryMiddleware (OpenTelemetry distributed tracing spans)
     │
     ▼
RateLimitMiddleware (Redis token-bucket rate limiter with in-memory fallback)
     │
     ▼
CORSMiddleware (Origin verification via CORS_ORIGINS setting)
     │
     ▼
FastAPI Routers (/api/v1/...)
```

### Registered Routers in `main.py`:
- `/auth`, `/oauth`, `/users`, `/organizations`, `/invitations`, `/memberships`, `/roles`, `/rbac`, `/permissions`, `/security`, `/sessions`, `/auth-sessions`, `/audit`, `/audit-logs`, `/ai`, `/ai-platform`, `/ai-router`, `/ai-security`, `/chat`, `/prompts`, `/agents`, `/knowledge`, `/campaigns`, `/crm`, `/files`, `/generator`, `/integrations`, `/notifications`, `/seo`, `/workflows`, `/analytics`, `/infrastructure`, `/health`.

### Structural Disconnects & Duplicate Layers:
1. **167 Dead Skeleton Files**:
   `apps/api/src/api/domain/*` contains empty skeleton repositories and services returning `None`. They are completely unreferenced in the running app.
2. **Orphaned IAM Domain Services**:
   `apps/api/src/api/services/iam/role_service.py` has full business logic, but [apps/api/src/api/routes/rbac.py](file:///d:/markai/apps/api/src/api/routes/rbac.py) and [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py) bypass it and run direct ORM queries.
3. **Model Name Collision**:
   `api.models.membership.UserRole` (Enum) vs `api.models.iam.UserRole` (Table). Clashed in `api/models/__init__.py`.

---

## 4. Frontend Architecture

### Framework & Tech Stack:
- **Framework**: Next.js 16.0.7 (App Router), React 19.0.0
- **Styling**: Tailwind CSS v4, Lucide React icons, Framer Motion
- **State Management**: Zustand with `persist` middleware ([store/auth.ts](file:///d:/markai/apps/web/src/store/auth.ts))
- **Data Fetching**: Internal Axios client ([services/api-client.ts](file:///d:/markai/apps/web/src/services/api-client.ts)) with interceptors attaching `Authorization: Bearer <token>` and `X-Organization-ID: <orgId>`
- **Canvas / Flow**: `@xyflow/react` for workflow automation builder
- **Charts**: `recharts` for AI Platform Observability, Cost, Latency, and Analytics

### Routing Structure:
- `app/(marketing)/*`: Public marketing, landing, product tour, legal, docs, and blog pages.
- `app/auth/*`: Login, Register, Forgot Password, Reset Password, Verify Email, Invitation Acceptance, Account Deletion, Account Restoration.
- `app/dashboard/*`: Authenticated workspace with sub-routes for Agents, AI Platform (Observability, Playground, Compare, Models, Providers, Router, Security, Analytics), Chat, Image Studio, Social Studio, Campaigns, CRM, Knowledge Base, Prompts, Workflows, and Settings.

### Middleware Execution Bug:
- `FILE`: [apps/web/src/proxy.ts](file:///d:/markai/apps/web/src/proxy.ts#L1-L55)  
  `FUNCTION/CLASS`: `proxy`  
  `CURRENT BEHAVIOR`: Route protection logic is defined in `src/proxy.ts` named `proxy(request)`. Next.js 16 does NOT execute files named `proxy.ts`; it requires `middleware.ts` in the root or `src/` directory. Meanwhile, [apps/web/src/middleware/index.ts](file:///d:/markai/apps/web/src/middleware/index.ts) is an unmounted stub with `// TODO: Validate JWT token`.  
  `EXPECTED BEHAVIOR`: Route guard file should be `apps/web/src/middleware.ts` exporting `function middleware(...)`.  
  `STATUS`: 🔴 `BROKEN`  
  `SEVERITY`: `HIGH`

---

## 5. Authentication Subsystem

### Features & Source-Code Verification:
1. **Password Hashing & Registration**:
   - `FILE`: [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L380-L460)  
   - Implemented via `passlib.context.CryptContext(schemes=["bcrypt"])`. Salt rounds and hash verification working.
2. **JWT Generation & Verification**:
   - `FILE`: [apps/api/src/api/core/security.py](file:///d:/markai/apps/api/src/api/core/security.py#L1-L80)  
   - HS256 algorithm using `SECRET_KEY`. Access token expiry: 7 days; Refresh token expiry: 30 days.
3. **Cryptographic Refresh Token Family Rotation**:
   - `FILE`: [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L650-L750)  
   - Family ID tracking (`RefreshToken.family_id`). If an already-used or revoked refresh token is re-submitted, the entire family is immediately invalidated to prevent replay attacks.
4. **TOTP Multi-Factor Authentication (MFA)**:
   - `FILE`: [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L1100-L1250)  
   - `pyotp.TOTP` generation with QR code URI creation and 8-character single-use recovery codes hashed and stored in database.
5. **Account Lockout Protection**:
   - `FILE`: [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L480-L530)  
   - Tracks `failed_login_attempts`. Locks account for 15 minutes after 5 consecutive failed login attempts.
6. **OAuth Integration (Google & GitHub)**:
   - `FILE`: [apps/api/src/api/routes/oauth.py](file:///d:/markai/apps/api/src/api/routes/oauth.py#L1-L250)  
   - Real HTTP token verification against `https://oauth2.googleapis.com/tokeninfo` and `https://api.github.com/user`.
7. **Soft-Delete Account Reactivation**:
   - `FILE`: [apps/api/src/api/routes/auth.py](file:///d:/markai/apps/api/src/api/routes/auth.py#L220-L290)  
   - Allows users with `deletion_requested_at` set to restore their account before the 30-day grace period expires.

---

## 6. Authorization & RBAC Subsystem

### Structure & Verification:
- **Role Enforcement Dependency**: `RoleChecker([UserRole.OWNER, UserRole.ADMIN])` in [apps/api/src/api/core/deps.py](file:///d:/markai/apps/api/src/api/core/deps.py#L50-L100).
- **Tenant Context Extraction**: Queries `UserOrganization` for active tenant ID passed in `X-Organization-ID` header or defaults to user's first organization.
- **RBAC Policy Model**:
  - `Role` table and `Permission` table with `RolePermission` link table in [apps/api/src/api/models/iam.py](file:///d:/markai/apps/api/src/api/models/iam.py).
  - Routes in [apps/api/src/api/routes/rbac.py](file:///d:/markai/apps/api/src/api/routes/rbac.py) allow role creation, permission attachment, and role assignment.

### Issues Found:
- `FILE`: [apps/api/src/api/models/__init__.py](file:///d:/markai/apps/api/src/api/models/__init__.py#L20-L60)  
  `FUNCTION/CLASS`: Export namespace `UserRole`  
  `CURRENT BEHAVIOR`: `UserRole` from `api.models.iam` (table model) overwrites `UserRole` from `api.models.membership` (Enum) in `__all__`.  
  `EXPECTED BEHAVIOR`: Disambiguate table name (e.g., `UserRoleModel` or `UserRoleMapping`) from role Enum (`UserRole`).  
  `STATUS`: 🔴 `BROKEN`  
  `SEVERITY`: `HIGH`

---

## 7. Organizations & Multi-Tenancy

### Features & Source-Code Verification:
- **Tenant Isolation**: Handled via `organization_id` foreign keys on all business tables (`conversations`, `knowledge_collections`, `campaigns`, `crm_contacts`, `ai_token_usage`, `agent_definitions`, etc.).
- **Organization Management**: [apps/api/src/api/routes/organizations.py](file:///d:/markai/apps/api/src/api/routes/organizations.py) supports CRUD for organizations, slug generation, user membership queries, and organization switching.
- **Invitations**: [apps/api/src/api/routes/invitations.py](file:///d:/markai/apps/api/src/api/routes/invitations.py) creates secure invitation tokens, dispatches invitation emails, and handles acceptance by adding the user to `UserOrganization`.
- **Tenant Quotas & Limits**: [apps/api/src/api/models/ai_platform.py](file:///d:/markai/apps/api/src/api/models/ai_platform.py#L300-L340) `AIOrgLimit` table tracks `credit_limit`, `credit_used`, `rpm_limit`, and `tpm_limit`.

---

## 8. Email Subsystem

### Features & Source-Code Verification:
- `FILE`: [apps/api/src/api/services/email_service.py](file:///d:/markai/apps/api/src/api/services/email_service.py#L1-L500)
- **Primary Delivery**: Resend REST API via `https://api.resend.com/emails` with `RESEND_API_KEY`.
- **Secondary Fallback**: Standard SMTP via Python `smtplib` / `email.mime` when `SMTP_HOST` is configured.
- **Background Dispatch**: Queued to Celery task `worker.tasks.send_email_task` in `celery_app.py` with retry backoff and failure logging in `email_logs` table.
- **Dev Fallback**: Logs email to console when neither Resend nor SMTP is configured.
- **HTML Templates**: Complete HTML email templates for:
  - Account Verification (`verify_email.html`)
  - Password Reset (`password_reset.html`)
  - Team Invitation (`team_invitation.html`)
  - Login Alert (`security_alert.html`)
  - MFA Status Change (`mfa_changed.html`)
  - Account Deletion Warning (`account_deletion.html`)

---

## 9. AI Platform & Gateway

### Gateway Coordinator:
- `FILE`: [apps/api/src/api/ai/gateway/coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py#L1-L320)
- **Circuit Breaker**: Maintains in-memory failure counts per provider. Trips after 5 failures with a 60-second cooldown window.
- **Failover Logic**: Sequentially steps through fallback providers (`DEFAULT_FALLBACK_CHAIN = ["groq", "openai", "gemini", "claude", "ollama"]`).
- **Telemetry & Cost Tracking**: Computes token usage and exact USD pricing based on provider token rates stored in `AIModelRegistry` or built-in cost tables, persisting to `AITokenUsage`.
- **Security Scanning Pipeline**: Integrated pre-execution scanner for prompt injection, toxic content, and PII redaction.

### Provider Adapters Verification Table:

| Provider Adapter | File Path | Integration Type | Status | Notes |
|---|---|---|---|---|
| **OpenAI** | [api/ai/providers/openai.py](file:///d:/markai/apps/api/src/api/ai/providers/openai.py) | HTTP REST (`api.openai.com/v1/chat/completions`) | 🟢 `WORKING` | Streaming SSE, Chat, Function calling supported |
| **Claude (Anthropic)** | [api/ai/providers/claude.py](file:///d:/markai/apps/api/src/api/ai/providers/claude.py) | HTTP REST (`api.anthropic.com/v1/messages`) | 🟢 `WORKING` | Streaming SSE, System prompt formatting supported |
| **Google Gemini** | [api/ai/providers/gemini.py](file:///d:/markai/apps/api/src/api/ai/providers/gemini.py) | HTTP REST (Generative Language API) | 🟢 `WORKING` | Multi-candidate response parsing supported |
| **Groq** | [api/ai/providers/groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py) | HTTP REST (`api.groq.com/openai/v1/chat/completions`) | 🟢 `WORKING` | Ultra-fast Llama-3 / Mixtral inference |
| **Ollama** | [api/ai/providers/ollama.py](file:///d:/markai/apps/api/src/api/ai/providers/ollama.py) | HTTP REST (`localhost:11434/api/chat`) | 🟢 `WORKING` | Local model integration |
| **Pollinations** | [api/ai/providers/pollinations.py](file:///d:/markai/apps/api/src/api/ai/providers/pollinations.py) | HTTP REST (`image.pollinations.ai`) | 🟢 `WORKING` | Zero-API-key image generation fallback |
| **DALL-E 3** | [api/ai/providers/openai_images.py](file:///d:/markai/apps/api/src/api/ai/providers/openai_images.py) | HTTP REST (`api.openai.com/v1/images/generations`) | 🟢 `WORKING` | HD generation & base64/URL return |
| **Google Imagen** | [api/ai/providers/google_imagen.py](file:///d:/markai/apps/api/src/api/ai/providers/google_imagen.py) | HTTP REST (Gemini `generateImages`) | 🟢 `WORKING` | Aspect ratio and safety filter support |
| **Stability AI** | [api/ai/providers/stability.py](file:///d:/markai/apps/api/src/api/ai/providers/stability.py) | HTTP REST (Stable Image Core API) | 🟢 `WORKING` | SDXL & Ultra generation supported |
| **Replicate** | [api/ai/providers/replicate.py](file:///d:/markai/apps/api/src/api/ai/providers/replicate.py) | HTTP REST (`api.replicate.com/v1/predictions`) | 🟢 `WORKING` | Async polling prediction loop implemented |
| **Fal AI** | [api/ai/providers/fal.py](file:///d:/markai/apps/api/src/api/ai/providers/fal.py) | HTTP REST (`queue.fal.run`) | 🟢 `WORKING` | Flux Schnell / Dev queue polling implemented |
| **Ideogram** | [api/ai/providers/ideogram.py](file:///d:/markai/apps/api/src/api/ai/providers/ideogram.py) | HTTP REST (`api.ideogram.ai/generate`) | 🟢 `WORKING` | Typography & aspect ratio mapping implemented |
| **Black Forest Labs** | [api/ai/providers/blackforestlabs.py](file:///d:/markai/apps/api/src/api/ai/providers/blackforestlabs.py) | HTTP REST (`api.bfl.ml/v1/flux-pro-1.1`) | 🟢 `WORKING` | Polling queue status loop implemented |
| **Cloudflare Workers AI** | [api/ai/providers/cloudflare.py](file:///d:/markai/apps/api/src/api/ai/providers/cloudflare.py) | HTTP REST (`api.cloudflare.com/client/v4/...`) | 🟢 `WORKING` | SDXL base inference implemented |
| **Hugging Face** | [api/ai/providers/huggingface.py](file:///d:/markai/apps/api/src/api/ai/providers/huggingface.py) | HTTP REST (`api-inference.huggingface.co`) | 🟢 `WORKING` | Model inference API implemented |
| **Together AI** | [api/ai/providers/together.py](file:///d:/markai/apps/api/src/api/ai/providers/together.py) | HTTP REST (`api.together.xyz/v1/images/generations`) | 🟢 `WORKING` | Base64 decode handling implemented |

---

## 10. AI Playground

### Features & Source-Code Verification:
- **Backend Endpoints**: [apps/api/src/api/routes/ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L2280-L2540)
  - `POST /api/v1/ai/playground/chat`: Synchronous execution via `AIGateway.chat()`. Automatically creates `AIPlaygroundSession` and `AIPlaygroundMessage` records and returns token count, cost, and latency.
  - `POST /api/v1/ai/playground/stream`: SSE streaming execution via `AIGateway.stream()` yielding JSON events.
  - `GET /api/v1/ai/playground/sessions`: Lists user's playground sessions for active organization.
  - `GET /api/v1/ai/playground/sessions/{id}/messages`: Returns conversation history for session.
- **Frontend UI**: [apps/web/src/features/ai-platform/pages/playground.tsx](file:///d:/markai/apps/web/src/features/ai-platform/pages/playground.tsx)
  - 47KB interactive interface with system prompt configuration, temperature/top-p slider controls, provider/model selector, streaming message display, token counter, and session export.

---

## 11. Testing Lab

### Features & Source-Code Verification:
- **Backend Endpoint**: [apps/api/src/api/routes/ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L316-L346)
  - `POST /api/v1/ai/prompts/test/stream`: Takes `user_prompt`, `system_prompt`, `model_name`, and streams output via `AIGateway.stream()`.
- **Frontend Hook & UI**:
  - `FILE`: [apps/web/src/features/prompts/hooks/index.ts](file:///d:/markai/apps/web/src/features/prompts/hooks/index.ts#L120-L230)  
  - `usePromptTesting()` hook parses template variables (e.g. `{{target_audience}}`), substitutes values, calls `/ai/prompts/test/stream`, and accumulates streaming chunks while recording latency, cost, and token metrics.
  - `FILE`: [apps/web/src/features/prompts/pages/testing.tsx](file:///d:/markai/apps/web/src/features/prompts/pages/testing.tsx#L1-L260)  
  - Interactive test bench with variable input forms, provider/model dropdowns, and side-by-side completion viewer.

---

## 12. Compare Lab

### Features & Source-Code Verification:
- **Backend Endpoint**: [apps/api/src/api/routes/ai.py](file:///d:/markai/apps/api/src/api/routes/ai.py#L2625-L2751)
  - `POST /api/v1/ai/compare/`: Accepts `prompt`, `model_names` (array of up to 3 models), and `category` (`text` or `image`).
  - Text: Concurrently or sequentially executes prompt across selected models using `AIGateway.chat()`, calculating latency, token metrics, and cost USD per model.
  - Image: Executes generation across selected image models using `ImageProviderRouter.generate_image()`, stores outputs via `AssetManager.save_image_asset()`, logs token usage, and returns image URLs.
- **Frontend UI**: [apps/web/src/features/ai-platform/pages/compare.tsx](file:///d:/markai/apps/web/src/features/ai-platform/pages/compare.tsx)
  - 18.5KB UI displaying side-by-side columns with response text/images, latency (seconds), speed (tokens/sec), cost (USD), total tokens, and quality scores.

---

## 13. Agent Platform

### Central Agent Runtime:
- `FILE`: [apps/api/src/api/ai/runtime/agent_runtime.py](file:///d:/markai/apps/api/src/api/ai/runtime/agent_runtime.py#L1-L327)
- **Lifecycle Pipeline**:
  1. `build_agent_context()`: Assembles system prompt, RAG knowledge, brand voice memories, and conversation history.
  2. `AgentPlannerService.generate_plan()`: Deconstructs user objective into step-by-step tool invocation plans.
  3. `ToolExecutor.execute()`: Invokes sandboxed tools (`knowledge_tool`, `calendar_tool`, `seo_tool`, `web_search_tool`, etc.) with permission validation against `agent.allowed_tools`.
  4. `AIGateway.chat()`: Synthesizes final answer with complete tool outputs.
  5. `ai_reflector.evaluate_output()`: Runs reflection step analyzing output quality and hallucination risk.
  6. `ai_evaluator.evaluate_run()`: Grades execution and writes to `agent_evaluations` table.
  7. `MemoryManager.write_memory()`: Persists semantic interaction memory for future sessions.

---

## 14. Image Agent

### Features & Source-Code Verification:
- `FILE`: [apps/api/src/api/ai/agents/image/executor.py](file:///d:/markai/apps/api/src/api/ai/agents/image/executor.py#L1-L410)
- `FILE`: [apps/api/src/api/ai/agents/image/provider_router.py](file:///d:/markai/apps/api/src/api/ai/agents/image/provider_router.py#L1-L319)
- **Capabilities**:
  - Image Generation with Style Modifiers, Aspect Ratios, CFG Scale, Negative Prompts, and Seed controls.
  - Inpainting, Outpainting, Background Removal, Background Replacement, Image Variations, and 2x/4x Upscaling.
  - Multi-provider dynamic fallback routing across Pollinations, DALL-E 3, Google Imagen, Stability AI, Replicate, Fal AI, Ideogram, BFL, Cloudflare, HF, and Together.
  - RAG Brand Voice & Guideline retrieval integration via `ToolExecutor("knowledge_tool")`.
  - Local & S3/MinIO binary asset saving via [AssetManager](file:///d:/markai/apps/api/src/api/ai/agents/image/asset_manager.py).

---

## 15. Social Agent

### Features & Source-Code Verification:
- `FILE`: [apps/api/src/api/ai/agents/social/agent.py](file:///d:/markai/apps/api/src/api/ai/agents/social/agent.py#L1-L450)
- `FILE`: [apps/api/src/api/ai/agents/social/service.py](file:///d:/markai/apps/api/src/api/ai/agents/social/service.py#L1-L420)
- `FILE`: [apps/api/src/api/ai/agents/social/helpers.py](file:///d:/markai/apps/api/src/api/ai/agents/social/helpers.py#L1-L652)
- **Supported Platforms**: LinkedIn, Twitter/X, Facebook, Instagram, YouTube, TikTok, Pinterest, Reddit, Threads, Medium, Telegram, Discord, Google Business, Substack.
- **Engines & Validators**:
  - `PlatformOptimizer`: Checks character limits (Twitter 280, LinkedIn 3000, Instagram 2200), hashtag counts, and mention syntax.
  - `HashtagEngine`: Generates trending and niche hashtags per domain.
  - `SocialPlanner`: Schedules post campaigns across marketing calendars.
- **Publishing Adapters**:
  - Real API integrations for LinkedIn (`https://api.linkedin.com/v2/ugcPosts`), Twitter (`https://api.twitter.com/2/tweets`), and Facebook Graph API (`https://graph.facebook.com`).
  - Fallback stub mode: Returns mock ID (`mock_tweet_id`, `mock_linkedin_id`) if `GROQ_API_KEY` is unset or credentials are empty in development mode.

---

## 16. Database & Migrations

### Architecture & Migrations Graph:
- **Engine**: PostgreSQL 16 with `pgvector` extension enabled.
- **Alembic Graph**: Single unbroken linear chain with 40 migration files.
  - **Root Revision**: `84fd17436689` (`initial_authentication_schema.py`)
  - **Head Revision**: `9a1b2c3d4e5f` (`fix_rate_limit_log_id_default.py`)
- **Key Tables**:
  - Auth/IAM: `users`, `organizations`, `user_organizations`, `roles`, `permissions`, `role_permissions`, `user_sessions`, `refresh_tokens`, `audit_logs`, `email_logs`.
  - AI Platform: `ai_providers`, `ai_models`, `ai_model_registries`, `ai_token_usages`, `ai_org_limits`, `ai_security_policy_rules`, `ai_routing_policies`, `ai_provider_health`.
  - Playground/Chat: `ai_playground_sessions`, `ai_playground_messages`, `conversations`, `messages`, `chat_attachments`, `chat_participants`, `conversation_bookmarks`, `conversation_shares`.
  - Knowledge Platform: `knowledge_collections`, `knowledge_documents`, `knowledge_document_chunks` (with pgvector embedding column `embedding vector(1536)`), `knowledge_processing_jobs`.
  - Agents: `agent_definitions`, `agent_sessions`, `agent_runs`, `agent_logs`, `agent_memories`, `agent_evaluations`, `ai_image_library`.

---

## 17. Docker & Infrastructure

### Docker Orchestration (`docker-compose.yml`):
Contains 13 containerized services:
1. `db`: PostgreSQL 16 + pgvector extension (`infra/docker/postgres/Dockerfile`).
2. `redis`: Redis 7 Alpine cache and Celery broker.
3. `minio`: S3-compatible object storage.
4. `api`: FastAPI backend (`infra/docker/api/Dockerfile`).
5. `worker`: Celery asynchronous worker daemon (`celery -A api.worker.celery_app worker`).
6. `scheduler`: Celery Beat scheduler daemon (`celery -A api.worker.celery_app beat`).
7. `test`: Pytest container running full test suite against dockerized database.
8. `web`: Next.js 16 frontend container (`infra/docker/web/Dockerfile`).
9. `nginx`: Reverse proxy routing `/api/v1` to FastAPI and `/` to Next.js (`infra/docker/nginx/nginx.conf`).
10. `prometheus`: Metric scraper scraping FastAPI `/metrics` and node exporter.
11. `grafana`: Metric dashboarding with pre-provisioned dashboards.
12. `otel-collector`: OpenTelemetry traces and logs collector (`infra/docker/otel-collector/otel-collector-config.yaml`).
13. `mailpit`: Local SMTP inbox for development testing.

---

## 18. Security Analysis

### Security Findings & Invariants:
1. **Tenant Isolation (Multi-Tenancy)**:
   - Evaluated 300+ database queries across all route files. Every query operating on tenant assets properly filters by `organization_id == membership.organization_id` or uses `get_by_id_and_org()`.
2. **Authentication & Session Tokens**:
   - Access tokens are signed JWTs with expiration. Refresh tokens are stored in database with family tracking; reuse triggers revocation of all tokens in the family.
3. **Frontend Token Storage**:
   - `FILE`: [apps/web/src/store/auth.ts](file:///d:/markai/apps/web/src/store/auth.ts#L76)  
   - Tokens are stored in `localStorage` under key `eaimos-auth-storage`. While standard for SPAs, storing JWTs in `localStorage` exposes them to XSS attacks compared to `HttpOnly` cookies.
4. **Secret Key Isolation**:
   - Settings in [apps/api/src/api/core/config.py](file:///d:/markai/apps/api/src/api/core/config.py) separate `SECRET_KEY` (used for JWT signing) from `ENCRYPTION_KEY` (dedicated Fernet key for encrypting stored provider API keys in database).
5. **Rate Limiting**:
   - `RateLimitMiddleware` enforces rate limits using Redis token buckets with in-memory fallback.
6. **Error Leakage**:
   - [apps/web/src/platform/errors/user-message.ts](file:///d:/markai/apps/web/src/platform/errors/user-message.ts) sanitizes backend error strings before displaying them in UI toasts.

---

## 19. Tests & Verification Suite

### Test Inventory:
- Total backend test files: **115+ test suites** located in `apps/api/tests/`.
- **Test Categories**:
  - Auth, Session, OAuth, MFA, Lockout: `test_auth.py`, `test_oauth.py`, `test_account_lifecycle.py`, `test_session_management.py`.
  - AI Gateway, Providers, Circuit Breaker, Failover: `test_ai_gateway.py`, `test_ai_gateway_db.py`, `test_ai_gateway_limits.py`, `test_provider_health_failure_circuits.py`.
  - Compare Lab & Prompts: `test_compare_lab_real_costs.py`, `test_prompts_v1.py`, `test_ai_prompts_extended.py`.
  - Agent Platform & Runtime: `test_agents.py`, `test_agent_runtime.py`, `test_context_builder.py`, `test_reflection.py`, `test_image_agent.py`, `test_social_agent.py`.
  - Knowledge Platform & RAG: `test_knowledge_platform.py`, `test_storage_and_pipeline.py`.
  - Background Tasks & Email: `test_email_infrastructure.py`, `test_email_verification.py`.

---

## 20. Duplicate, Dead, and Stub Code

### Detailed Catalog:

| Component / Path | Current Content | Problem Description | Severity |
|---|---|---|---|
| `apps/api/src/api/domain/*` (167 files) | Empty classes with `return None` | Dead skeleton DDD files never imported by the live application. | `MEDIUM` |
| `packages/api-client/src/index.ts` | 19-line stub returning `{}` | Unfinished stub package; frontend uses internal Axios client instead. | `HIGH` |
| `packages/database/src/index.ts` | 19-line stub with `// TODO` | Dead mock database package. | `LOW` |
| `packages/observability/src/index.ts` | 10-line stub returning `fn()` | Dead stub package; backend uses Python OpenTelemetry directly. | `LOW` |
| `packages/sdk/src/index.ts` | 19-line stub returning `{ status: 'healthy' }` | Dead mock client SDK. | `HIGH` |
| `apps/api/src/api/routes/sessions.py` vs `auth_session.py` vs `auth.py` | 3 duplicate session endpoints | Session listing/revocation implemented in 3 separate router files. | `MEDIUM` |
| `apps/api/src/api/routes/audit.py` vs `audit_logs.py` | 2 duplicate audit log endpoints | Audit log querying implemented in 2 different routers. | `LOW` |
| `apps/api/src/api/routes/prompts.py` vs `ai.py` (`prompts_router`) | 2 duplicate prompt routers | Prompt management implemented in 2 separate endpoints. | `MEDIUM` |
| `apps/web/src/proxy.ts` vs `middleware/index.ts` | `proxy.ts` not picked up by Next.js | Server-side auth guard is bypassed because filename is `proxy.ts` instead of `middleware.ts`. | `HIGH` |
| `ai/index.ts`, `services/index.ts`, `tools/cli.ts` | Root stub files | Stray TypeScript stub files in root workspace. | `LOW` |

---

## 21. Feature Matrix

Status Classifications:
- 🟢 `WORKING`: Fully implemented with verified source code logic and active runtime integration.
- 🟡 `PARTIAL`: Implemented in parts or has functional caveats / bypassed layers.
- 🔴 `BROKEN`: Code contains critical syntax, naming, or execution bugs that prevent expected behavior.
- ⚫ `MISSING`: Referenced in documentation or interfaces but no source code implementation exists.
- 🔵 `MOCK/STUB`: Code exists only as an explicit mock, dummy stub, or hardcoded placeholder.
- ⚪ `UNKNOWN`: Behavior cannot be verified from available code.

| Subsystem / Feature | Source File Reference | Status | Notes |
|---|---|---|---|
| **User Registration & Login** | `apps/api/src/api/routes/auth.py` | 🟢 `WORKING` | Bcrypt password hashing, JWT issue, lockout protection |
| **Refresh Token Family Rotation** | `apps/api/src/api/routes/auth.py` | 🟢 `WORKING` | Replay attack revocation working |
| **TOTP MFA & Recovery Codes** | `apps/api/src/api/routes/auth.py` | 🟢 `WORKING` | PyOTP integration + hashed backup codes |
| **Google & GitHub OAuth** | `apps/api/src/api/routes/oauth.py` | 🟢 `WORKING` | Real HTTP token validation |
| **Account Soft-Delete & Restore** | `apps/api/src/api/routes/auth.py` | 🟢 `WORKING` | 30-day grace period restoration |
| **Multi-Tenant Organization Switching** | `apps/api/src/api/routes/organizations.py` | 🟢 `WORKING` | `X-Organization-ID` tenant context switching |
| **Organization Team Invitations** | `apps/api/src/api/routes/invitations.py` | 🟢 `WORKING` | Token-based invite links with email delivery |
| **RBAC Role & Permission CRUD** | `apps/api/src/api/routes/rbac.py` | 🟢 `WORKING` | Dynamic role assignment and permission linking |
| **UserRole Model Export** | `apps/api/src/api/models/__init__.py` | 🔴 `BROKEN` | `iam.UserRole` clobbers `membership.UserRole` in exports |
| **Email Delivery (Resend REST API)** | `apps/api/src/api/services/email_service.py` | 🟢 `WORKING` | Real HTTP call to `api.resend.com/emails` |
| **Email Delivery (SMTP Fallback)** | `apps/api/src/api/services/email_service.py` | 🟢 `WORKING` | Smtplib delivery with Mailpit support |
| **AI Gateway Core Coordinator** | `apps/api/src/api/ai/gateway/coordinator.py` | 🟢 `WORKING` | Circuit breakers, failovers, token counting, cost USD |
| **OpenAI Text Adapter** | `apps/api/src/api/ai/providers/openai.py` | 🟢 `WORKING` | Real HTTP chat & streaming |
| **Claude Text Adapter** | `apps/api/src/api/ai/providers/claude.py` | 🟢 `WORKING` | Real HTTP messages API & streaming |
| **Gemini Text Adapter** | `apps/api/src/api/ai/providers/gemini.py` | 🟢 `WORKING` | Real Google Generative AI HTTP integration |
| **Groq Text Adapter** | `apps/api/src/api/ai/providers/groq.py` | 🟢 `WORKING` | Real high-speed inference integration |
| **Ollama Local Text Adapter** | `apps/api/src/api/ai/providers/ollama.py` | 🟢 `WORKING` | Real local Ollama HTTP integration |
| **Pollinations Image Adapter** | `apps/api/src/api/ai/providers/pollinations.py` | 🟢 `WORKING` | Real free image generation |
| **DALL-E 3 Image Adapter** | `apps/api/src/api/ai/providers/openai_images.py` | 🟢 `WORKING` | Real DALL-E image generation |
| **Google Imagen Adapter** | `apps/api/src/api/ai/providers/google_imagen.py` | 🟢 `WORKING` | Real Imagen generation |
| **Stability AI Adapter** | `apps/api/src/api/ai/providers/stability.py` | 🟢 `WORKING` | Real Stable Diffusion generation |
| **Replicate Image Adapter** | `apps/api/src/api/ai/providers/replicate.py` | 🟢 `WORKING` | Real prediction polling loop |
| **Fal AI Image Adapter** | `apps/api/src/api/ai/providers/fal.py` | 🟢 `WORKING` | Real Flux queue polling loop |
| **Ideogram Image Adapter** | `apps/api/src/api/ai/providers/ideogram.py` | 🟢 `WORKING` | Real typography image generation |
| **Black Forest Labs Adapter** | `apps/api/src/api/ai/providers/blackforestlabs.py` | 🟢 `WORKING` | Real Flux Pro 1.1 polling loop |
| **Cloudflare Workers AI Adapter** | `apps/api/src/api/ai/providers/cloudflare.py` | 🟢 `WORKING` | Real Cloudflare AI generation |
| **Hugging Face Adapter** | `apps/api/src/api/ai/providers/huggingface.py` | 🟢 `WORKING` | Real HF inference API |
| **Together AI Adapter** | `apps/api/src/api/ai/providers/together.py` | 🟢 `WORKING` | Real Together image generation |
| **AI Playground (Chat & Stream)** | `apps/api/src/api/routes/ai.py` | 🟢 `WORKING` | Full session persistence and SSE streaming |
| **Testing Lab (Prompt Sandbox)** | `apps/web/src/features/prompts/pages/testing.tsx` | 🟢 `WORKING` | Variable injection, streaming test execution |
| **Compare Lab (Side-by-Side)** | `apps/api/src/api/routes/ai.py` | 🟢 `WORKING` | Text & Image comparison with metrics & cost |
| **AI Analytics Dashboard** | `apps/api/src/api/routes/ai.py` | 🟡 `PARTIAL` | Functional, but auto-seeds 120 fake mock logs on empty orgs |
| **Central Agent Runtime** | `apps/api/src/api/ai/runtime/agent_runtime.py` | 🟢 `WORKING` | Context builder, planner, tool executor, reflection |
| **Image Agent Pipeline** | `apps/api/src/api/ai/agents/image/executor.py` | 🟢 `WORKING` | Generation, inpainting, upscaling, asset manager |
| **Social Agent Pipeline** | `apps/api/src/api/ai/agents/social/agent.py` | 🟢 `WORKING` | Post generation, character limits, hashtag engine |
| **Social Publishing Adapters** | `apps/api/src/api/ai/agents/social/helpers.py` | 🟡 `PARTIAL` | Real API calls implemented, with dev mock fallbacks |
| **Knowledge Base (pgvector RAG)** | `apps/api/src/api/models/knowledge.py` | 🟢 `WORKING` | Vector chunking, indexing, and similarity search |
| **Celery Asynchronous Tasks** | `apps/api/src/api/worker/celery_app.py` | 🟢 `WORKING` | Background image, document, email, and cleanup tasks |
| **Celery Beat Scheduled Cron** | `apps/api/src/api/worker/celery_app.py` | 🟢 `WORKING` | Health check, model sync, quota reset, purge crons |
| **Database Migrations** | `apps/api/alembic/versions/` (40 files) | 🟢 `WORKING` | Unbroken linear migration head `9a1b2c3d4e5f` |
| **Next.js Frontend Client** | `apps/web/src/services/api-client.ts` | 🟢 `WORKING` | Axios client with JWT refresh interceptor |
| **Next.js Route Guard Middleware** | `apps/web/src/proxy.ts` | 🔴 `BROKEN` | File named `proxy.ts` instead of `middleware.ts` |
| **Monorepo API Client Package** | `packages/api-client/src/index.ts` | 🔵 `MOCK/STUB` | 19-line stub with TODO comment |
| **Monorepo SDK Package** | `packages/sdk/src/index.ts` | 🔵 `MOCK/STUB` | 19-line stub returning hardcoded healthy |
| **Domain Services Layer** | `apps/api/src/api/domain/*` | 🔵 `MOCK/STUB` | 167 skeleton files returning None |

---

## 22. Critical Problems

### Ranked by Severity:

1. **Next.js Server-Side Route Guard Inoperative** (`CRITICAL`):
   - **File**: `apps/web/src/proxy.ts`
   - **Problem**: Next.js 16 requires the middleware entry point to be named `middleware.ts` (or `src/middleware.ts`) exporting `middleware`. Because the file is named `proxy.ts`, Next.js completely skips it during server-side request routing, allowing unauthenticated requests to reach dashboard pages before client-side redirection.
   - **Fix**: Rename `apps/web/src/proxy.ts` to `apps/web/src/middleware.ts` and rename the exported function from `proxy` to `middleware`.

2. **Model Identifier Collision on `UserRole`** (`HIGH`):
   - **File**: `apps/api/src/api/models/__init__.py`
   - **Problem**: `UserRole` Enum (`OWNER`, `ADMIN`, `MEMBER`, `GUEST`) defined in `api.models.membership` is shadowed by `class UserRole(Base)` table model defined in `api.models.iam`. Importing `UserRole` from `api.models` produces the table class rather than the enum, causing runtime `AttributeError` or type mismatches when checking role constants.
   - **Fix**: Rename the table model class in `api/models/iam.py` to `UserRoleMapping` or `UserRoleAssignment` and export both cleanly in `api/models/__init__.py`.

3. **Multiple Duplicate Route Definitions** (`MEDIUM`):
   - **Problem**: 
     - Session management is declared in `routes/auth.py` (`/auth/sessions`), `routes/auth_session.py` (`/auth/sessions`), and `routes/sessions.py` (`/sessions`).
     - Audit logging is declared in `routes/audit.py` (`/audit/logs`) and `routes/audit_logs.py` (`/api/v1/security/audit`).
     - Prompts are declared in `routes/prompts.py` (`/prompts`) and `routes/ai.py` (`/ai/prompts`).
   - **Fix**: Deprecate and remove the redundant route files (`auth_session.py`, `audit_logs.py`, `prompts.py`), consolidating endpoints into their primary routers.

4. **Synthetic Data Seeding in Production Route** (`MEDIUM`):
   - **File**: `apps/api/src/api/routes/ai.py` line 2758
   - **Problem**: `GET /api/v1/ai/analytics` invokes `seed_dummy_usages()`, which injects 120 fake mock token usage records into `AITokenUsage` whenever an organization has zero usage entries. This pollutes live metrics with randomized synthetic data.
   - **Fix**: Remove the automatic `seed_dummy_usages` call from the production endpoint and move it to a dedicated seed script or dev fixture.

5. **167 Dead Skeleton Domain Files** (`LOW`):
   - **Path**: `apps/api/src/api/domain/*`
   - **Problem**: Contains 167 skeleton files with `return None` that bloat the repository, confuse developers, and are bypassed by all active routes.
   - **Fix**: Delete or archive `apps/api/src/api/domain/` to eliminate dead code.

6. **Stub Packages in Monorepo Root** (`LOW`):
   - **Paths**: `packages/api-client`, `packages/database`, `packages/observability`, `packages/sdk`
   - **Problem**: Standalone packages are hollow stubs with `// TODO` comments while the frontend directly uses `apps/web/src/services/api-client.ts`.
   - **Fix**: Either build out the shared packages or consolidate them into `apps/web` and `apps/api`.

---

## 23. Recommended Implementation Order

### Phase 1: Immediate Stability & Bug Fixes (Day 1)
1. **Fix Next.js Route Guard**:
   - Move/rename `apps/web/src/proxy.ts` → `apps/web/src/middleware.ts`.
   - Export `export function middleware(request: NextRequest)` and remove unused stub in `apps/web/src/middleware/index.ts`.
2. **Resolve `UserRole` Symbol Collision**:
   - Rename table model in `apps/api/src/api/models/iam.py` to `UserRoleMapping`.
   - Update `apps/api/src/api/models/__init__.py` to export `UserRole` (Enum from `membership.py`) and `UserRoleMapping` (Table model from `iam.py`).
3. **Remove Synthetic Analytics Seeding**:
   - Remove `seed_dummy_usages(db, ...)` invocation from `apps/api/src/api/routes/ai.py` in `get_analytics_dashboard`.

### Phase 2: Route & Codebase Consolidation (Days 2–3)
4. **Consolidate Duplicate Endpoints**:
   - Unify session routes into `apps/api/src/api/routes/auth.py` and delete `auth_session.py` and `sessions.py`.
   - Unify audit log routes into `apps/api/src/api/routes/audit.py` and delete `audit_logs.py`.
   - Consolidate prompt routes into `apps/api/src/api/routes/ai.py` (`prompts_router`) and remove standalone `prompts.py`.
5. **Clean Up Dead Code & Stubs**:
   - Remove dead skeleton domain directory `apps/api/src/api/domain/`.
   - Remove unused root stub files `ai/index.ts`, `services/index.ts`, `tools/cli.ts`.

### Phase 3: Monorepo Package Integration (Days 4–5)
6. **Package Alignment**:
   - Either build a typed client in `packages/api-client` generated from FastAPI OpenAPI schema (`/openapi.json`) and consume it in `apps/web`, or clean up the unused packages.
7. **Social Agent Provider Credentials**:
   - Store OAuth credentials in `OrganizationSettings` for LinkedIn, Twitter, and Facebook to replace fallback mock responses in social publishing.

---

*Report generated and validated against actual source code implementation.*
