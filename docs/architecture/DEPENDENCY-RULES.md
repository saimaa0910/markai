# Architecture Dependency Rules & Fitness Checks

**System**: Enterprise AI Marketing Operating System (EAIMOS / MarkAI)  
**Status**: APPROVED & FROZEN  
**Date**: August 31, 2026  

---

## 1. Layer Dependency Direction

Dependencies must strictly flow inward from the external transport layer to the core domain and infrastructure.

```
API Transport Layer (routes)
         │
         ▼
Application Services (services, ai gateway, agent runtime)
         │
         ▼
Domain Layer (models, entities, policies)
         │
         ▼
Repositories & Ports (repositories)
         │
         ▼
Infrastructure & External Adapters (providers, database, redis, celery, minio)
```

### Invariant Rules:
1. **Core Cannot Depend Outward**: `api.core` must never import `api.routes`, `api.services`, or `api.repositories`.
2. **Domain Models Cannot Depend on Transport**: `api.models` must never import `api.routes` or `api.schemas`.
3. **Repositories Cannot Depend on Routes**: `api.repositories` must never import `api.routes`.
4. **Transport Cannot Bypass Services**: Routes must not perform raw database mutations, business calculations, or direct third-party API calls.
5. **No AI Provider Calls Outside AIGateway**: No route, studio, or service may instantiate or call an AI provider directly.

---

## 2. Forbidden Import Matrix

| Source Module | Prohibited Target Modules | Rationale |
|---|---|---|
| `api.core.*` | `api.routes.*`, `api.services.*`, `api.repositories.*` | Core shared infrastructure must remain independent. |
| `api.models.*` | `api.routes.*`, `api.services.*`, `api.schemas.*` | Domain entities must not couple to HTTP presentation layers. |
| `api.repositories.*` | `api.routes.*`, `api.ai.providers.*` | Persistence abstractions must not depend on transport or AI providers. |
| `api.ai.providers.*` | `api.routes.*`, `api.models.*`, `apps.web.*` | Provider adapters must remain pure HTTP execution contracts. |
| `api.ai.runtime.*` | Domain-specific agents (e.g. `api.ai.agents.image.*`) | Generic Agent Runtime must not couple to specific agent implementations. |
| `apps/web/*` (Frontend) | `apps/api/*`, PostgreSQL, Redis, Celery | Frontend must communicate with backend strictly via HTTP REST API. |

---

## 3. Cross-Domain Communication Rules

1. **In-Process Service Calls**: When one domain context needs data or actions from another (e.g., `Campaigns` needing `CRM Contact` emails), it must invoke the target domain's published **Service Interface** (e.g., `ContactService.get_contacts_by_org()`), never direct table writes across domains.
2. **Event-Driven Decoupling**: For asynchronous cross-domain updates (e.g., User registered → dispatch welcome email, Document indexed → notify search cache), domains should dispatch background Celery tasks or use the Transactional Outbox.
3. **No Cross-Tenant Queries**: Every cross-domain service call MUST pass `organization_id` as an explicit parameter.

---

## 4. Automated Architecture Fitness Tests

The repository includes automated Architecture Fitness Tests in `apps/api/tests/test_architecture_fitness.py` to prevent architecture drift during CI/CD execution:

```python
import ast
import os
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "api"))

def get_python_files(subpath: str):
    target_dir = os.path.join(ROOT_DIR, subpath)
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)

def parse_imports(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module

def test_core_does_not_import_routes():
    """Rule 1: api.core must never import api.routes."""
    for file in get_python_files("core"):
        for imp in parse_imports(file):
            assert not imp.startswith("api.routes"), f"Violation in {file}: imports {imp}"

def test_models_do_not_import_routes():
    """Rule 2: api.models must never import api.routes."""
    for file in get_python_files("models"):
        for imp in parse_imports(file):
            assert not imp.startswith("api.routes"), f"Violation in {file}: imports {imp}"

def test_repositories_do_not_import_routes():
    """Rule 3: api.repositories must never import api.routes."""
    for file in get_python_files("repositories"):
        for imp in parse_imports(file):
            assert not imp.startswith("api.routes"), f"Violation in {file}: imports {imp}"

def test_providers_do_not_import_routes():
    """Rule 4: api.ai.providers must never import api.routes."""
    for file in get_python_files("ai/providers"):
        for imp in parse_imports(file):
            assert not imp.startswith("api.routes"), f"Violation in {file}: imports {imp}"
```

---

## 5. Monorepo Package Governance (The Three-Use Rule)

1. **Standalone Package Creation Threshold**: A new package in `packages/*` is permitted ONLY if it satisfies the **Three-Use Rule** (consumed by at least 3 separate applications/services) or represents an external SDK.
2. **Elimination of Hollow Stubs**: Packages containing only placeholder files or `// TODO` stubs must not be referenced by application entry points.
3. **Internal vs Shared Code**: Code used exclusively by `apps/web` must live in `apps/web/src/`. Code used exclusively by `apps/api` must live in `apps/api/src/api/`.
