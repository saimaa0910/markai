# AI Agent Engine & Tooling Documentation

## Architectural Overview

The **AI Agent Subsystem** in **MarkAI** provides autonomous agent planning, tool binding, stateful step execution, and context memory retention.

---

## Agent Runtime Architecture

```mermaid
graph TD
    UserGoal[User Objective Input] --> AgentExecutor[Agent Executor Service\nservices/agent_executor.py]
    AgentExecutor --> MemoryManager[Memory Manager\nservices/memory_manager.py]
    MemoryManager -->|Fetch Short & Long-term Context| AgentExecutor
    
    AgentExecutor --> Planner[Agent Planner\nservices/agent_planner.py]
    Planner -->|Generate Execution Plan| AgentExecutor

    subgraph Step Execution Loop
        AgentExecutor -->|Step Action| ToolRegistry[Tool Registry\nai/tools/registry.py]
        ToolRegistry --> CRMTool[CRM Tool\nai/tools/crm_tool.py]
        ToolRegistry --> RAGTool[Knowledge RAG Tool\nai/tools/knowledge_tool.py]
        ToolRegistry --> WebSearch[Web Search Tool\nai/tools/web_search_tool.py]
        ToolRegistry --> WorkflowTool[Workflow Tool\nai/tools/workflow_tool.py]
    end

    Step Execution Loop -->|Step Result| AgentExecutor
    AgentExecutor -->|Update Agent Session & Run State| DB[(PostgreSQL Database)]
```

---

## Component Specifications

### 1. Agent Planner (`api.services.agent_planner`)
- Breaks goals into discrete action steps.
- Formats step objects with `step_index`, `action_type`, `tool_name`, `tool_input_schema`, and `expected_output`.

### 2. Agent Executor (`api.services.agent_executor`)
- Executes agent sessions synchronously or via Celery background workers (`agent_run_task`).
- Retries step execution up to `max_retries` configuration.
- Maintains `AgentExecution` logs detailing step results and token consumption.

### 3. Tool Registry & Tool Bindings (`api.ai.tools`)
- **`CRMTool`** ([crm_tool.py](file:///d:/markai/apps/api/src/api/ai/tools/crm_tool.py)): Allows agents to create/lookup CRM leads, contacts, and record activity logs.
- **`KnowledgeTool`** ([knowledge_tool.py](file:///d:/markai/apps/api/src/api/ai/tools/knowledge_tool.py)): Allows agents to perform semantic search queries against organization knowledge bases.
- **`WebSearchTool`** ([web_search_tool.py](file:///d:/markai/apps/api/src/api/ai/tools/web_search_tool.py)): Allows agents to retrieve public search information.
- **`WorkflowTool`** ([workflow_tool.py](file:///d:/markai/apps/api/src/api/ai/tools/workflow_tool.py)): Allows agents to trigger external or internal graph automation workflows.

### 4. Memory Manager (`api.services.memory_manager`)
- **Short-Term Conversational Memory**: Preserves message history per session.
- **Episodic & Long-Term Memory**: Stores structured key-value state facts across agent runs for specific users/organizations.
