# Workflow Automation Engine

## Overview

The **Workflow Engine** in **MarkAI** ([workflow_engine.py](file:///d:/markai/apps/api/src/api/services/workflow_engine.py)) executes declarative, node-based automation pipelines. Workflows allow users to chain together AI Agent runs, tool calls, data transformations, and notifications.

---

## Workflow Execution Flow

```mermaid
graph TD
    Trigger[Trigger Event / Manual API / Cron] --> CreateExec[Create WorkflowExecution\nStatus: PENDING]
    CreateExec --> RunEngine[WorkflowEngine.run_workflow()]
    
    subgraph Step Loop
        RunEngine --> CreateStep[Create WorkflowStep Record\nStatus: RUNNING]
        
        CreateStep --> CheckType{Check Step Type}
        CheckType -->|step_type == agent_run| ExecAgent[AgentExecutorService.run_agent_session()]
        CheckType -->|step_type == tool_call| ExecTool[ToolExecutor.execute()]
        CheckType -->|step_type == notify| DispatchNotification[NotificationService / In-App]
        
        ExecAgent --> UpdateContext[Pass Output to Step Context\ncontext[step_id] = output]
        ExecTool --> UpdateContext
        DispatchNotification --> UpdateContext
        
        UpdateContext --> MarkStepComplete[Mark WorkflowStep COMPLETED]
    end

    MarkStepComplete --> NextStep{More Steps remaining?}
    NextStep -->|Yes| CreateStep
    NextStep -->|No| FinalizeExec[Mark WorkflowExecution COMPLETED]
```

---

## Supported Step Types

1. **`agent_run`**:
   - Executes an autonomous AI Agent session for a specified `agent_id`.
   - Templated input parameters (e.g. `{{previous_step_id}}`) are dynamically interpolated with accumulated step outputs in `context`.
2. **`tool_call`**:
   - Direct execution of system tools via `ToolExecutor` ([registry.py](file:///d:/markai/apps/api/src/api/ai/tools/registry.py)).
   - Supports tool execution for `CRMTool`, `KnowledgeTool`, `WebSearchTool`, and sub-workflows.
3. **`notify`**:
   - Dispatches in-app or email notifications to organization users.

---

## Error Handling & Status Tracking

- **Execution Statuses** (`ExecutionStatus` Enum): `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`.
- **Step Latency Tracking**: Tracks `latency_ms` per step and total pipeline runtime.
- **Rollback & Failure Propagation**: If any step raises an exception, `db_step.status` is set to `FAILED`, the error message is recorded, and the overall execution status is marked `FAILED`.
