"""
Workflow Tool — Executes a declarative workflow platform execution step.
"""
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from api.ai.tools import BaseTool, ToolInput, ToolResult


class WorkflowTool(BaseTool):
    @property
    def name(self) -> str:
        return "workflow_tool"

    @property
    def description(self) -> str:
        return (
            "Trigger a workflow defined in the enterprise platform, pass inputs, "
            "and retrieve the execution outputs. Use this tool to trigger business workflows, "
            "automation sequences, database pipelines, or integration jobs."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "The UUID of the workflow definition to trigger.",
                },
                "input_data": {
                    "type": "object",
                    "description": "A dictionary of input key-value variables passed to the workflow.",
                    "default": {},
                },
                "wait_for_completion": {
                    "type": "boolean",
                    "description": "Whether to wait synchronously for the workflow execution to finish.",
                    "default": True,
                },
            },
            "required": ["workflow_id"],
        }

    def execute(self, input: ToolInput, db: Session) -> ToolResult:
        try:
            org_id = uuid.UUID(input.organization_id)
            user_id = uuid.UUID(input.user_id)
            
            wf_id_str = input.params.get("workflow_id")
            if not wf_id_str:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="workflow_id parameter is required"
                )
                
            wf_id = uuid.UUID(wf_id_str)
            input_data = input.params.get("input_data", {})
            wait_for_completion = input.params.get("wait_for_completion", True)

            from api.models.workflow import WorkflowDefinition, WorkflowExecution

            # 1. Verify workflow definition exists and belongs to the org
            wf = (
                db.query(WorkflowDefinition)
                .filter(
                    WorkflowDefinition.id == wf_id,
                    WorkflowDefinition.organization_id == org_id,
                    WorkflowDefinition.deleted_at.is_(None),
                )
                .first()
            )
            if not wf:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error=f"Workflow definition '{wf_id_str}' not found in your organization."
                )

            # 2. Create execution entry
            execution = WorkflowExecution(
                workflow_id=wf_id,
                organization_id=org_id,
                triggered_by=user_id,
                input_data=input_data,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # 3. Synchronous execution if wait_for_completion is True
            if wait_for_completion:
                from api.services.workflow_engine import WorkflowEngine
                result = WorkflowEngine.run_workflow(db=db, execution=execution)
                
                return ToolResult(
                    success=(result.status.value == "COMPLETED"),
                    tool_name=self.name,
                    output={
                        "execution_id": str(result.id),
                        "status": result.status.value,
                        "error_message": result.error_message,
                        "output_data": {
                            step.step_id: step.output_data 
                            for step in result.steps
                        } if hasattr(result, "steps") else {}
                    },
                    metadata={"execution_id": str(result.id)}
                )
            else:
                # Dispatch asynchronously
                return ToolResult(
                    success=True,
                    tool_name=self.name,
                    output={
                        "execution_id": str(execution.id),
                        "status": "QUEUED",
                        "message": "Workflow execution triggered asynchronously."
                    },
                    metadata={"execution_id": str(execution.id)}
                )

        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=str(e))
