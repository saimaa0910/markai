# Enterprise Source Code Audit - Performance Audit

## Performance Audit Summary

| Finding | Severity | Evidence | Files |
| :--- | :--- | :--- | :--- |
| **Missing Indexing on Foreign Keys** | 🟡 Medium | Relationships link tables via UUID foreign keys, but several intermediate models lack index declarations on foreign keys. This will cause slow queries as tables grow. | [ai_platform.py](file:///d:/markai/apps/api/src/api/models/ai_platform.py) |
| **N+1 Query Issues** | 🟡 Medium | SQLAlchemy relationships do not define explicit loading strategies (e.g. `lazy="joined"` or `selectinload`), causing default lazy loading and potential N+1 query patterns. | [agent.py](file:///d:/markai/apps/api/src/api/models/agent.py#L115-L118) |
| **Blocking HTTP Calls** | 🟡 Medium | `GroqProvider` and other providers make blocking HTTP calls using `httpx.Client()` in the synchronous request flow instead of using async clients. | [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L12-L44) |
| **Simulated Embedding Performance** | ✓ Secure | Hashing-based embeddings are extremely fast, but it is a mockup, not a real neural embedding query. | [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py#L103-L123) |
| **Next.js Bundle Size Concerns** | 🟡 Medium | Visual modules like `recharts` and `@xyflow/react` are loaded eagerly, which increases initial JS bundle sizes. | [package.json](file:///d:/markai/apps/web/package.json#L17-L27) |

------------------------------------------------------------

## Detailed Findings

### 1. Database Indexing Gaps
While major model tables like `users` have partial indexes, several relational mappings (e.g. `ai_provider_keys`, `ai_provider_health`, `ai_requests`) lack indexes on foreign keys (`provider_id`, `organization_id`, etc.). This will cause table scans during joins as databases grow.
> [!TIP]
> Ensure all foreign keys used in SQL joins have explicit index declarations in SQLAlchemy models.

### 2. Blocking HTTP Client Calls
In [groq.py](file:///d:/markai/apps/api/src/api/ai/providers/groq.py), the client uses `httpx.Client` (synchronous) instead of `httpx.AsyncClient` inside the FastAPI endpoints. When multiple concurrent requests hit FastAPI, the synchronous HTTP calls block the main event loop thread:
```python
class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = httpx.Client(timeout=30.0) # Blocking sync client
```
This reduces overall system throughput.
> [!IMPORTANT]
> Propose refactoring providers to use `httpx.AsyncClient` for all outbound API requests.
