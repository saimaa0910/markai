# Service Catalog & Business Logic Layer

## Overview

The Service Layer residing in `apps/api/src/api/services/` contains the core business logic of **MarkAI**. Services act as orchestrators between API controllers, AI provider subsystems, database repositories, background task queues, and external APIs.

---

## Complete Service Catalog

### 1. `AgentExecutor` ([agent_executor.py](file:///d:/markai/apps/api/src/api/services/agent_executor.py))
- **Purpose**: Stateful execution engine for autonomous AI agents.
- **Methods**: `execute_agent_run()`, `execute_step()`, `evaluate_tool_call()`, `finalize_run()`.
- **Dependencies**: `AgentPlanner`, `AIGatewayCoordinator`, `MemoryManager`, `ToolRegistry`.
- **Consumers**: `routes/agents.py`, `worker/celery_app.py`.

### 2. `AgentPlanner` ([agent_planner.py](file:///d:/markai/apps/api/src/api/services/agent_planner.py))
- **Purpose**: Deconstructs user objectives into discrete action steps.
- **Methods**: `generate_plan()`, `refine_plan()`.
- **Dependencies**: `AIGatewayCoordinator`.
- **Consumers**: `AgentExecutor`.

### 3. `RAGEngine` ([rag_engine.py](file:///d:/markai/apps/api/src/api/services/rag_engine.py))
- **Purpose**: Executes hybrid dense semantic and sparse keyword retrieval for RAG.
- **Methods**: `query_knowledge_base()`, `rank_chunks()`, `build_context_window()`.
- **Dependencies**: `VectorStoreService`, `DocumentProcessor`, `KnowledgeRepository`.
- **Consumers**: `routes/knowledge.py`, `tools/knowledge_tool.py`.

### 4. `VectorStoreService` ([vector_store.py](file:///d:/markai/apps/api/src/api/services/vector_store.py))
- **Purpose**: Generates vector embeddings and performs vector similarity search.
- **Methods**: `generate_embeddings()`, `upsert_vectors()`, `similarity_search()`.
- **Dependencies**: Numpy, OpenAI Embedding API / Local Embedding Provider.
- **Consumers**: `RAGEngine`, `document_processing.py`.

### 5. `DocumentParser` ([document_parser.py](file:///d:/markai/apps/api/src/api/services/document_parser.py))
- **Purpose**: Parses uploaded raw files into clean plain text.
- **Methods**: `parse_pdf()`, `parse_docx()`, `parse_txt()`, `parse_csv()`.
- **Dependencies**: PyPDF2, python-docx.
- **Consumers**: `routes/knowledge.py`, `routes/files.py`.

### 6. `WorkflowEngine` ([workflow_engine.py](file:///d:/markai/apps/api/src/api/services/workflow_engine.py))
- **Purpose**: Executes directed node-graph automation pipelines.
- **Methods**: `run_workflow()`, `evaluate_node()`, `evaluate_condition()`.
- **Dependencies**: SQLAlchemy Session, `QueueService`.
- **Consumers**: `routes/workflows.py`, `tools/workflow_tool.py`.

### 7. `PromptService` ([prompt.py](file:///d:/markai/apps/api/src/api/services/prompt.py))
- **Purpose**: Template rendering, versioning, and test execution.
- **Methods**: `create_prompt()`, `create_version()`, `render_template()`, `execute_prompt()`.
- **Dependencies**: `AIGatewayCoordinator`.
- **Consumers**: `routes/ai.py`.

### 8. `MemoryManager` ([memory_manager.py](file:///d:/markai/apps/api/src/api/services/memory_manager.py))
- **Purpose**: Stores and retrieves agent context and user memory state.
- **Methods**: `get_session_memory()`, `add_memory()`, `summarize_memory()`.
- **Dependencies**: `AIGatewayCoordinator`, SQLAlchemy.
- **Consumers**: `AgentExecutor`, `routes/memory.py`.

### 9. `AnalyticsService` ([analytics_service.py](file:///d:/markai/apps/api/src/api/services/analytics_service.py))
- **Purpose**: Aggregates platform token usage, cost distribution, and user counts.
- **Methods**: `get_token_usage_stats()`, `get_cost_breakdown()`, `get_active_users()`.
- **Dependencies**: SQLAlchemy ORM.
- **Consumers**: `routes/analytics.py`, `routes/observability.py`.

### 10. `CacheService` ([cache_service.py](file:///d:/markai/apps/api/src/api/services/cache_service.py))
- **Purpose**: Fast key-value caching layer over Redis.
- **Methods**: `get()`, `set()`, `delete()`, `get_json()`, `set_json()`.
- **Dependencies**: `redis_manager.py`.
- **Consumers**: `AIGatewayCoordinator`, `routes/auth.py`.

### 11. `NotificationService` ([notification_service.py](file:///d:/markai/apps/api/src/api/services/notification_service.py))
- **Purpose**: In-app notifications and SMTP email delivery.
- **Methods**: `send_email()`, `create_notification()`, `mark_as_read()`.
- **Dependencies**: Smtplib, Pydantic.
- **Consumers**: `routes/notifications.py`, `AlertEngine`.

### 12. `IntegrationService` ([integration_service.py](file:///d:/markai/apps/api/src/api/services/integration_service.py))
- **Purpose**: Connector service for third-party platforms (Slack, HubSpot, Salesforce).
- **Methods**: `connect_integration()`, `sync_data()`, `dispatch_webhook()`.
- **Dependencies**: `httpx`.
- **Consumers**: `routes/integrations.py`.
