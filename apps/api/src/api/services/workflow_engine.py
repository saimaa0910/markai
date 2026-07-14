import uuid
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.models.workflow import WorkflowDefinition, WorkflowExecution, WorkflowStep, ExecutionStatus
from api.repositories.agent import agent_definition_repo, agent_session_repo
from api.services.agent_executor import AgentExecutorService
from api.ai.tools.registry import ToolExecutor


class WorkflowEngine:
    """
    Core executor engine for managing and executing declarative workflows.
    Supports running sequential steps, handling task failures, and passing context.
    """

    @staticmethod
    def run_workflow(
        db: Session,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        start_time = time.perf_counter()
        execution.status = ExecutionStatus.RUNNING
        db.commit()

        workflow: WorkflowDefinition = execution.workflow
        steps_def = workflow.steps_definition or []
        context = dict(execution.input_data or {})

        tool_executor = ToolExecutor(db)

        try:
            for step_config in steps_def:
                step_id = step_config.get("id")
                step_type = step_config.get("type")
                params = step_config.get("params", {})

                # 1. Create Workflow Step run record
                db_step = WorkflowStep(
                    execution_id=execution.id,
                    organization_id=execution.organization_id,
                    step_id=step_id,
                    step_type=step_type,
                    status=ExecutionStatus.RUNNING,
                    input_data=params,
                )
                db.add(db_step)
                db.commit()
                db.refresh(db_step)

                step_start = time.perf_counter()

                try:
                    # 2. Execute Step by type
                    if step_type == "agent_run":
                        agent_id_str = params.get("agent_id")
                        agent_id = uuid.UUID(agent_id_str)
                        # Find or create a session for workflow execution
                        # We scope it to the workflow execution so it's isolated
                        from api.models.agent import AgentSession
                        session = (
                            db.query(AgentSession)
                            .filter(
                                AgentSession.agent_id == agent_id,
                                AgentSession.organization_id == execution.organization_id,
                                AgentSession.title == f"Workflow-{workflow.name}-{execution.id}",
                            )
                            .first()
                        )
                        if not session:
                            session = AgentSession(
                                agent_id=agent_id,
                                user_id=execution.triggered_by or execution.organization_id, # Fallback to org UUID if manual background
                                organization_id=execution.organization_id,
                                title=f"Workflow-{workflow.name}-{execution.id}",
                            )
                            db.add(session)
                            db.commit()
                            db.refresh(session)

                        # Render input text with context placeholders
                        input_tmpl = params.get("input_template", "{{input}}")
                        for k, v in context.items():
                            input_tmpl = input_tmpl.replace(f"{{{{{k}}}}}", str(v))

                        run = AgentExecutorService.run_agent_session(
                            db=db, session=session, user_input=input_tmpl
                        )

                        if run.status == "FAILED":
                            raise RuntimeError(f"Agent failed to execute: {run.error_message}")

                        db_step.output_data = {"output": run.agent_output}
                        context[step_id] = run.agent_output

                    elif step_type == "tool_call":
                        tool_name = params.get("tool_name")
                        tool_params = dict(params.get("tool_params", {}))

                        # Variable replacement in tool params
                        for pk, pv in list(tool_params.items()):
                            if isinstance(pv, str):
                                for k, v in context.items():
                                    pv = pv.replace(f"{{{{{k}}}}}", str(v))
                                tool_params[pk] = pv

                        res = tool_executor.execute(
                            tool_name=tool_name,
                            params=tool_params,
                            organization_id=str(execution.organization_id),
                            user_id=str(execution.triggered_by or execution.organization_id),
                        )

                        if not res.success:
                            raise RuntimeError(f"Tool execution failed: {res.error}")

                        db_step.output_data = {"output": res.output}
                        context[step_id] = res.output

                    elif step_type == "notify":
                        notification_title = params.get("title", "Workflow Alert")
                        notification_body = params.get("body", "")
                        for k, v in context.items():
                            notification_body = notification_body.replace(f"{{{{{k}}}}}", str(v))

                        # Dispatch In-App Notification directly
                        from api.models.integration import Notification, NotificationPriority, NotificationChannel
                        notification = Notification(
                            user_id=execution.triggered_by or execution.organization_id,
                            organization_id=execution.organization_id,
                            title=notification_title,
                            body=notification_body,
                            channel=NotificationChannel.IN_APP,
                            priority=NotificationPriority.MEDIUM,
                        )
                        db.add(notification)
                        db.commit()

                        db_step.output_data = {"success": True}

                    else:
                        raise ValueError(f"Unknown workflow step type: {step_type}")

                    db_step.status = ExecutionStatus.COMPLETED
                    db_step.latency_ms = int((time.perf_counter() - step_start) * 1000)
                    db.commit()

                except Exception as step_exc:
                    db_step.status = ExecutionStatus.FAILED
                    db_step.error_message = str(step_exc)
                    db_step.latency_ms = int((time.perf_counter() - step_start) * 1000)
                    db.commit()
                    raise step_exc

            # Completed all steps successfully
            execution.status = ExecutionStatus.COMPLETED
            execution.output_data = context
            execution.latency_ms = int((time.perf_counter() - start_time) * 1000)
            db.commit()
            return execution

        except Exception as e:
            db.rollback()
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.latency_ms = int((time.perf_counter() - start_time) * 1000)
            db.commit()
            return execution
