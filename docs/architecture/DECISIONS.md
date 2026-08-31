# Architectural Decision Records (ADRs)

**System**: Enterprise AI Marketing Operating System (EAIMOS / MarkAI)  
**Status**: APPROVED & FROZEN  
**Date**: August 31, 2026  

---

## Index of Architectural Decisions

- [ADR-001: Adoption of Modular Monolith over Microservices](#adr-001-adoption-of-modular-monolith-over-microservices)
- [ADR-002: Central AI Gateway as Unified AI Execution Plane](#adr-002-central-ai-gateway-as-unified-ai-execution-plane)
- [ADR-003: Generic Agent Runtime with Capability Manifests & Sandboxed Tools](#adr-003-generic-agent-runtime-with-capability-manifests--sandboxed-tools)
- [ADR-004: PostgreSQL + pgvector as Primary Relational and Vector Store](#adr-004-postgresql--pgvector-as-primary-relational-and-vector-store)
- [ADR-005: Server-Side Tenant Context Enforcement & IDOR Invariant](#adr-005-server-side-tenant-context-enforcement--idor-invariant)
- [ADR-006: Centralized IAM with Refresh Token Family Rotation and MFA](#adr-006-centralized-iam-with-refresh-token-family-rotation-and-mfa)
- [ADR-007: Asynchronous Processing via Celery and Redis](#adr-007-asynchronous-processing-via-celery-and-redis)
- [ADR-008: Next.js 16 Feature-Based Frontend Architecture](#adr-008-nextjs-16-feature-based-frontend-architecture)
- [ADR-009: Monorepo Governance and the Three-Use Rule for Shared Packages](#adr-009-monorepo-governance-and-the-three-use-rule-for-shared-packages)
- [ADR-010: Dual-Tier Error Handling Contract](#adr-010-dual-tier-error-handling-contract)
- [ADR-011: Transactional Outbox Pattern for Resilient Event Delivery](#adr-011-transactional-outbox-pattern-for-resilient-event-delivery)

---

## ADR-001: Adoption of Modular Monolith over Microservices

### Context
EAIMOS requires high cohesion between IAM, AI routing, knowledge embeddings, CRM, marketing campaigns, and workflow automation. Splitting these domains into separate microservices prematurely introduces severe operational overhead, distributed transaction complexities, network latency, and deployment friction without any immediate scalability justification.

### Decision
We formally adopt a **Modular Monolith** architecture implemented as a single FastAPI backend application. Domain modules are structured with clear internal boundaries and explicit service interfaces. Distributed microservices are strictly prohibited.

### Consequences
- **Positive**: Single unified deployment, atomic database migrations, low latency in-process calls, simplified testing, shared connection pools.
- **Negative**: Requires strict static analysis and code discipline to prevent domain coupling and circular dependencies.

---

## ADR-002: Central AI Gateway as Unified AI Execution Plane

### Context
Various modules (Playground, Testing Lab, Compare Lab, Image Studio, Social Studio, Agent Platform, and Chat) require access to text and image AI models. Implementing independent provider calls in each studio or route leads to duplicated API key handling, inconsistent circuit breaking, lack of unified token cost calculation, and disjointed telemetry.

### Decision
All AI model invocations across all capabilities (Text, Image, Vision, Embeddings, Audio, Multimodal) MUST route exclusively through the centralized `AIGateway` (`apps/api/src/api/ai/gateway/coordinator.py`) and its unified `ProviderRouter` and `ProviderRegistry`. Direct HTTP calls to provider APIs from routes, studios, or agents are strictly forbidden.

### Consequences
- **Positive**: Single point of control for circuit breaking, fallback failover, dynamic key decryption, security scanning (prompt injection/PII), OpenTelemetry spans, and Prometheus metric aggregation.
- **Negative**: All new provider integrations must conform to the unified `BaseProvider` adapter interface.

---

## ADR-003: Generic Agent Runtime with Capability Manifests & Sandboxed Tools

### Context
Hardcoding domain-specific branching (e.g. `if agent_type == 'image': ... elif agent_type == 'social': ...`) inside the core agent runtime destroys extensibility and couples the execution engine to specific product features.

### Decision
The `AgentRuntime` (`apps/api/src/api/ai/runtime/agent_runtime.py`) MUST remain completely generic. Agent domain specialization is achieved strictly through:
1. **Agent Manifests**: Static or database-driven metadata defining system prompts and capabilities.
2. **Context Builder**: Dynamic assembly of system instructions, RAG knowledge, brand voice memories, and history.
3. **Sandboxed Tools**: Discrete tools registered in `ToolExecutor` and authorized per agent definition.
4. **Post-Execution Evaluation**: Pluggable reflection and evaluation scoring.

### Consequences
- **Positive**: Adding new agent types (e.g. Video Agent, Analytics Agent) requires zero changes to the core execution engine.
- **Negative**: Complex agent flows must be expressible as discrete tool calls and planning steps.

---

## ADR-004: PostgreSQL + pgvector as Primary Relational and Vector Store

### Context
Managing separate database engines for relational metadata (e.g., PostgreSQL) and vector embeddings (e.g., Pinecone, Qdrant, Milvus) increases infrastructure complexity and prevents atomic transactions between document metadata and chunk embeddings. Introducing SQLite in production creates concurrency bottlenecks and type inconsistencies.

### Decision
We standardize on **PostgreSQL 16** with the **pgvector** extension as the single source of truth for both relational entities and vector embeddings (`knowledge_document_chunks.embedding vector(1536)`). SQLite is prohibited in production and local development.

### Consequences
- **Positive**: Transactional consistency between documents and chunks, unified backups, unified Alembic migrations, reduced operational footprint.
- **Negative**: Requires PostgreSQL with `pgvector` pre-installed in container images.

---

## ADR-005: Server-Side Tenant Context Enforcement & IDOR Invariant

### Context
In a multi-tenant SaaS platform, client-supplied resource IDs must never be trusted without validating tenant ownership. Relying on frontend route guards or client headers alone exposes the system to Insecure Direct Object References (IDOR) and cross-tenant data leaks.

### Decision
Tenant isolation is enforced server-side at the repository and service levels. Every request to an organization-scoped resource requires:
1. Validating that the authenticated user possesses active membership in the target organization (`UserOrganization`).
2. Scoping all database SELECT, UPDATE, and DELETE operations with `organization_id == active_tenant_id`.

### Consequences
- **Positive**: Zero possibility of IDOR or cross-tenant data leakage.
- **Negative**: Every repository query and data model must explicitly include and filter by `organization_id`.

---

## ADR-006: Centralized IAM with Refresh Token Family Rotation and MFA

### Context
Authentication vulnerabilities such as token theft, session hijacking, and brute force credential stuffing represent critical risks for enterprise marketing systems.

### Decision
IAM is centralized with the following security invariants:
1. Passwords hashed using bcrypt with salt.
2. Short-lived signed JWT access tokens (7 days maximum).
3. Cryptographic Refresh Token Family rotation: reusing an already-rotated refresh token instantly invalidates the entire family.
4. Account lockout for 15 minutes after 5 consecutive failed login attempts.
5. Standard TOTP MFA (RFC 6238) with single-use hashed recovery backup codes.
6. 30-day soft-delete grace period allowing account restoration before permanent purge.

### Consequences
- **Positive**: Enterprise-grade security posture meeting compliance standards.
- **Negative**: Requires database tracking for active sessions and refresh token families.

---

## ADR-007: Asynchronous Processing via Celery and Redis

### Context
Long-running operations such as PDF vector chunking, AI image generation, bulk campaign email broadcasts, and scheduled account purging exceed standard HTTP request timeouts (30-60s) and degrade web server concurrency if executed synchronously.

### Decision
All operations exceeding 3 seconds or requiring background scheduling MUST be dispatched as asynchronous tasks to **Celery workers** backed by **Redis** as the message broker and result backend. Periodic tasks are managed via **Celery Beat**.

### Consequences
- **Positive**: Immediate HTTP responses, resilient retries with exponential backoff, background job status tracking via `AIBackgroundJob`.
- **Negative**: Requires running separate worker and scheduler container processes.

---

## ADR-008: Next.js 16 Feature-Based Frontend Architecture

### Context
A flat or arbitrary frontend structure causes component bloat, duplicated API calls, disjointed state management, and maintenance headaches.

### Decision
The frontend (`apps/web`) is structured using a **Feature-Based Architecture**:
- `apps/web/src/app/`: Next.js App Router route entry points and layouts.
- `apps/web/src/features/<domain>/`: Self-contained feature modules containing components, hooks, stores, and types.
- `apps/web/src/services/api-client.ts`: Centralized Axios client handling JWT attachment and automatic token refresh.
- `apps/web/src/store/auth.ts`: Centralized Zustand authentication store.

### Consequences
- **Positive**: Clear domain ownership, modular code co-location, maintainable UI components.
- **Negative**: Developers must organize code by feature rather than dumping components into a global folder.

---

## ADR-009: Monorepo Governance and the Three-Use Rule for Shared Packages

### Context
Creating multiple hollow packages (e.g. `packages/api-client`, `packages/database`, `packages/sdk`) without meaningful usage creates monorepo overhead, version drift, and confusion when the actual application implements its own internal clients.

### Decision
We adopt the **Three-Use Rule**: A shared package in `packages/*` is created and maintained ONLY when it has at least three distinct consumers or represents an externalized public SDK with a dedicated build pipeline. Hollow stubs must not be added to the repository.

### Consequences
- **Positive**: Cleaner dependency tree, zero phantom package maintenance.
- **Negative**: Utilities remain localized within `apps/api` or `apps/web` until genuine multi-package reuse is established.

---

## ADR-010: Dual-Tier Error Handling Contract

### Context
Raw backend exceptions expose sensitive system internals (database schema, SQL syntax, file paths, credentials), while generic errors provide poor debugging ergonomics for clients.

### Decision
We enforce a **Dual-Tier Error Handling Contract**:
1. **Backend**: Emits structured machine-readable error envelopes with standard HTTP status codes, correlation IDs, and error codes (`{"detail": "...", "code": "..."}`).
2. **Frontend**: Passes all API errors through `getSafeErrorMessage()` to sanitize error strings before displaying UI toasts, logging full diagnostic details only to telemetry.

### Consequences
- **Positive**: Zero information leakage to end-users; robust telemetry for operators.
- **Negative**: Requires consistent exception wrapping in API services and middleware.

---

## ADR-011: Transactional Outbox Pattern for Resilient Event Delivery

### Context
In-memory event buses lose events during application crashes or restarts. Directly publishing to external brokers inside a database transaction risks dual-write inconsistencies if the database commit fails after the message is published.

### Decision
For events requiring guaranteed cross-process delivery (such as webhook notifications, audit log synchronization, and external marketing syncs), we establish the **Transactional Outbox Pattern**: events are written to an `outbox_events` database table within the same transaction as business data, and polled/dispatched by a background Celery worker.

### Consequences
- **Positive**: At-least-once delivery guarantee, atomic transactions, no lost events.
- **Negative**: Requires outbox table management and periodic cleanup of processed events.
