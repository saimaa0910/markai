# Testing Suite & Coverage Inventory

## Overview

The backend test suite in **MarkAI** consists of **30 test files** located in `apps/api/tests/`. Tests are run using `pytest` against an isolated test database (`_temp_test_db.db` / SQLite in-memory).

---

## Test Infrastructure & Fixtures (`conftest.py`)

- **Database Fixture** (`db_session`): Creates a fresh SQLAlchemy test session for every test function and rolls back changes upon completion.
- **Client Fixture** (`client`): FastAPI `TestClient` instance configured for making mock HTTP requests.
- **Authenticated User Fixtures** (`auth_headers`, `test_user`, `test_org`): Automatically seeds an admin user, organization tenant, and returns valid JWT Authorization Bearer headers for testing protected routes.

---

## Test Suite Inventory

| Test File | Target Subsystem | Key Test Scenarios | Source Link |
| :--- | :--- | :--- | :--- |
| `test_auth.py` | Auth & Security | User registration, login token generation, token refresh, invalid credentials | [test_auth.py](file:///d:/markai/apps/api/tests/test_auth.py) |
| `test_phase2_auth_orgs.py` | Organizations & RBAC | Multi-tenant organization creation, user membership assignment, role permissions | [test_phase2_auth_orgs.py](file:///d:/markai/apps/api/tests/test_phase2_auth_orgs.py) |
| `test_ai_gateway.py` | AI Gateway 2.0 | Multi-provider completion requests, provider status verification | [test_ai_gateway.py](file:///d:/markai/apps/api/tests/test_ai_gateway.py) |
| `test_ai_gateway_db.py` | AI Gateway DB | Usage log persistence, token calculation, SSE response format | [test_ai_gateway_db.py](file:///d:/markai/apps/api/tests/test_ai_gateway_db.py) |
| `test_ai_gateway_limits.py` | Gateway Limits | Rate limiting enforcement, daily token budget ceilings | [test_ai_gateway_limits.py](file:///d:/markai/apps/api/tests/test_ai_gateway_limits.py) |
| `test_ai_router_phase1b.py` | Enterprise Router | Cost minimization, latency minimization, fallback cascades | [test_ai_router_phase1b.py](file:///d:/markai/apps/api/tests/test_ai_router_phase1b.py) |
| `test_ai_security_phase1c.py` | Security Scanner | Prompt injection detection, PII masking, system prompt protection | [test_ai_security_phase1c.py](file:///d:/markai/apps/api/tests/test_ai_security_phase1c.py) |
| `test_agents.py` | AI Agents | Agent creation, configuration persistence, goal execution | [test_agents.py](file:///d:/markai/apps/api/tests/test_agents.py) |
| `test_agents_extended.py` | Agent Planning | Multi-step planning, tool selection, session execution | [test_agents_extended.py](file:///d:/markai/apps/api/tests/test_agents_extended.py) |
| `test_tools.py` | Agent Tools | CRMTool, KnowledgeTool, WebSearchTool, WorkflowTool bindings | [test_tools.py](file:///d:/markai/apps/api/tests/test_tools.py) |
| `test_knowledge_platform.py` | Knowledge & RAG | Document parsing, text chunking, vector similarity search | [test_knowledge_platform.py](file:///d:/markai/apps/api/tests/test_knowledge_platform.py) |
| `test_workflows.py` | Workflow Engine | Sequential node execution, condition evaluation, step state | [test_workflows.py](file:///d:/markai/apps/api/tests/test_workflows.py) |
| `test_crm.py` | CRM Engine | Lead creation, contact updates, company relations, activity logs | [test_crm.py](file:///d:/markai/apps/api/tests/test_crm.py) |
| `test_campaigns.py` | Campaigns | Marketing campaign flows, stage transitions | [test_campaigns.py](file:///d:/markai/apps/api/tests/test_campaigns.py) |
| `test_generator.py` | Content Generator | Template rendering, multi-variant marketing copy generation | [test_generator.py](file:///d:/markai/apps/api/tests/test_generator.py) |
| `test_observability.py` | Observability | Prometheus metric scraping, OpenTelemetry span creation | [test_observability.py](file:///d:/markai/apps/api/tests/test_observability.py) |
| `test_main.py` | System Readiness | `/health`, `/live`, `/ready` readiness checks | [test_main.py](file:///d:/markai/apps/api/tests/test_main.py) |

---

## Testing Gaps & Recommendations

1. **Frontend Integration / E2E Tests**: Frontend (`apps/web`) currently lacks Playwright or Cypress End-to-End tests.
2. **Mocking External Provider APIs**: Several AI Gateway tests rely on mock responses when provider keys are absent; adding explicit `vcrpy` or `pytest-mock` fixtures will increase isolation.
