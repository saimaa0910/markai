# Enterprise Source Code Audit - Testing Audit

## Testing Overview

- **Unit & Integration Tests**: 480 test cases are collected under `apps/api/tests/` and domain sub-folders, testing routes, services, schemas, and repository layer functions.
- **Frontend Tests**: Visual unit tests are located under feature test files (e.g. `features/crm/tests/crm.test.ts`), verifying hook mutations and state slices.
- **E2E Tests**: Found in `tests/e2e.test.ts` (skeleton mock).

------------------------------------------------------------

## Test Case Distribution & Frameworks
The testing framework consists of:
1. **pytest** (Backend): Uses pytest plugins `anyio` and `asyncio` for asynchronous test isolation.
2. **SQLite in-memory shared cache**: Configured in [tests/conftest.py](file:///d:/markai/apps/api/tests/conftest.py#L32-L37) to mock PostgreSQL, creating tables before run and dropping them after completion.
3. **Vitest / Jest** (Frontend): Tests React Hooks, Zustand store mutations, and schema validators.

------------------------------------------------------------

## Test Suite Verification Results
The test suite was executed dynamically and returned the following metrics:
- **Total test cases**: 480
- **Passed**: 478
- **Failed**: 2
- **Warnings**: 633
- **Execution Duration**: 1757.91s (~29 minutes)

### Test Failure Breakdown

#### 1. `test_list_agent_templates` Failure
- **File**: `tests/test_agents_extended.py`
- **Error**: `AssertionError: assert 5 == 3`
- **Root Cause**: The test checks that the `/api/v1/agents/templates` endpoint returns exactly 3 default templates ("Content Agent", "SEO Agent", "Campaign Agent"). However, the server actually returns 5 templates (including new templates added in later sprints, e.g. "Image Agent" and "Social Agent").

#### 2. `test_fallback_to_groq_when_no_rules_exist` Failure
- **File**: `tests/test_sprint_7_3_production_ai.py`
- **Error**: `AssertionError: assert 'google' == 'groq'`
- **Root Cause**: The Model Router's default candidate routing list falls back to `google` models when no active organization routing rules match, but the test expected it to fall back to `groq` as the default.

---

## Mock Quality Analysis
Mocks are configured in [conftest.py](file:///d:/markai/apps/api/tests/conftest.py):
- **Redis Mocking**: Replaces the RedisConnectionManager instance with a local dictionary `MockRedisClient` mapping `get` / `set` / `delete` / `keys` calls.
- **AI Provider Mocking**: Dynamically replaces methods of `OpenAIProvider`, `GroqProvider`, `ClaudeProvider`, `GeminiProvider`, and `OpenRouterProvider` with mock handlers:
  - `mock_chat`: returns a simulated text block containing model configuration tags.
  - `mock_stream`: yields a mock generator chunk `[Simulated chunk]`.
  - `mock_embeddings`: yields a static array of size 1536 containing `0.1` values.
  - `mock_vision`: returns a static text block.
  - `mock_json_output`: returns a mock JSON string `"{}"`.
- **Outbound HTTP / Search Mocking**: Monkeypatches `httpx.get` calls matching `duckduckgo.com` to return simulated HTML tags for search queries.
- **MinIO S3 Mocking**: Substitutes `minio.Minio` client with `MockMinioClient` which stores uploaded buffer bytes in local dictionaries.

> [!NOTE]
> The mocks are very comprehensive and allow testing complex run pipelines without internet connections. However, they hide potential API integration errors (e.g. model response schemas drift, API authentication failures). During execution, database log saves in middleware output warnings: `sqlite3.OperationalError: table ai_logs has no column named version` due to discrepancies in model properties vs the SQLite test tables creation.

------------------------------------------------------------

## Missing Test Cases
1. **SSO / OAuth**: Tests cover basic password logins, but OAuth flows are not tested.
2. **Real RAG Search**: Retrieval is only tested against simulated MD5 hashing embeddings, not real PostgreSQL pgvector searches.
3. **Queue Workers**: The Celery worker is run eagerly in tests (`task_always_eager=True`), meaning asynchronous concurrency bugs are not covered.

