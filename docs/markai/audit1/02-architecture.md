# Enterprise Source Code Audit - Architecture Audit

## Architecture Overview

| Component | Status | Evidence | Files |
| :--- | :--- | :--- | :--- |
| **Layer Separation** | 🟡 Partial | Distinct `routes`, `services`, `repositories`, and `models` exist, but service logic occasionally leaks into API routes directly (e.g. `routes/generator.py` queries database and makes direct LLM calls instead of using `ContentGenerationService`). | [generator.py](file:///d:/markai/apps/api/src/api/routes/generator.py), [content_generator.py](file:///d:/markai/apps/api/src/api/models/content_generator.py) |
| **Dependency Direction** | ✓ Fully Implemented | Core components follow clean inward-pointing dependency flows. Router depends on domain controllers/services; services depend on repositories; repositories depend on models. | [deps.py](file:///d:/markai/apps/api/src/api/core/deps.py), [session.py](file:///d:/markai/apps/api/src/api/database/session.py) |
| **Module Boundaries** | ✓ Fully Implemented | Domains under `d:\markai\apps\api\src\api\domain` isolate distinct sub-systems (`analytics`, `auth`, `billing`, `campaigns`, `crm`, `integrations`, `knowledge`, `notifications`, `organizations`, `users`, `workflow`). | [domain/](file:///d:/markai/apps/api/src/api/domain) |
| **Circular Dependencies** | ✓ Fully Implemented | No circular references detected in imports due to lazy imports inside functions where necessary. E.g. in `coordinator.py`, providers are imported inside `__init__` and `_get_provider_adapter`. | [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py#L24-L32) |
| **Shared Utilities** | ✓ Fully Implemented | Backend utilities like cryptography and custom JSON serializers are cleanly separated in `api/core` and `api/utils`. Frontend shared UI is placed in `@eaimos/ui`. | [security.py](file:///d:/markai/apps/api/src/api/core/security.py), [encryption.py](file:///d:/markai/apps/api/src/api/core/encryption.py) |
| **Service Boundaries** | 🟡 Partial | Business rules are cleanly structured under domains, but some packages (e.g. `packages/database`, `packages/api-client`) are stubs and bypassed in favor of local code blocks. | [database/index.ts](file:///d:/markai/packages/database/src/index.ts) |
| **Repositories** | ✓ Fully Implemented | Repository pattern handles data persistence layer. A unified Unit of Work handles multi-repository transactions. | [unit_of_work.py](file:///d:/markai/apps/api/src/api/repositories/unit_of_work.py), [base.py](file:///d:/markai/apps/api/src/api/repositories/base.py) |
| **Dependency Injection** | ✓ Fully Implemented | FastAPI relies on `Depends` wrappers for session mappings, roles, security validations, and current user retrieval. | [deps.py](file:///d:/markai/apps/api/src/api/core/deps.py) |
| **Configuration** | ✓ Fully Implemented | Settings are dynamically loaded from environment variables using Pydantic BaseSettings, with manual root `.env` loading as fallback. | [config.py](file:///d:/markai/apps/api/src/api/core/config.py) |
| **Feature Isolation** | ✓ Fully Implemented | Frontend Next.js follows a strict feature-driven module system. Pages, components, hooks, mutations, and stores are isolated per feature directory. | [features/](file:///d:/markai/apps/web/src/features) |
| **Plugin Architecture** | ❌ Missing | No dynamic runtime plugin loader exists. All models, providers, and workflow executors are statically hardcoded in Python modules. | [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py) |

------------------------------------------------------------

## Layer Separation & Dependency Injection (DI)
The backend project adheres to standard FastAPI dependency injection patterns using:
- **FastAPI Depends**: Injected dependencies reside under `api/core/deps.py`. Example: `get_current_user` retrieves the user by verifying JWT signatures, fetching the record from `db_session`.
- **Database Session Contexts**: `get_db` dependency in `api/database/session.py` acts as a request-scoped database context manager, ensuring connection pools are recycled properly.

## Feature Isolation (Frontend)
The React frontend isolates elements into self-contained directory hierarchies. For example, `src/features/crm/` contains:
- `components/` (UI components)
- `hooks/` (custom React hooks)
- `mutations/` (REST mutations)
- `queries/` (REST queries)
- `store/` (Zustand client state slices)
- `validators/` (Zod schemas)

This isolates logic completely from other features.
