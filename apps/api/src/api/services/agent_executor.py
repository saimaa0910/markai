import uuid
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentRunStatus
from api.repositories.agent import agent_run_repo, agent_log_repo
from api.services.agent_planner import AgentPlannerService
from api.services.memory_manager import MemoryManager
from api.ai.tools.registry import ToolExecutor
from api.ai.gateway.coordinator import AIGateway


class AgentExecutorService:
    """
    Main runtime execution service for running agent sessions.
    Responsible for plan creation, tool dispatch, logging, and state synchronization.
    """

    @staticmethod
    def run_agent_session(
        db: Session,
        session: AgentSession,
        user_input: str,
    ) -> AgentRun:
        start_time = time.perf_counter()

        # 1. Create run record
        run = AgentRun(
            session_id=session.id,
            organization_id=session.organization_id,
            user_input=user_input,
            status=AgentRunStatus.RUNNING,
            iterations=0,
            total_tokens=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        tool_executor = ToolExecutor(db)
        gateway = AIGateway()
        agent = session.agent

        try:
            # Step A: Log thought start
            AgentExecutorService._log_step(
                db=db,
                run_id=run.id,
                org_id=session.organization_id,
                step_type="thought",
                content="Analyzing user input and generating execution plan...",
            )

            # Step B: Call Planner
            plan = AgentPlannerService.generate_plan(
                db=db,
                agent=agent,
                user_input=user_input,
                session_id=session.id,
                organization_id=session.organization_id,
                user_id=session.user_id,
            )
            run.plan = plan
            db.commit()

            thought = plan.get("thought", "Determining next steps...")
            steps = plan.get("steps", [])

            AgentExecutorService._log_step(
                db=db,
                run_id=run.id,
                org_id=session.organization_id,
                step_type="thought",
                content=thought,
                metadata={"plan": plan},
            )

            # Step C: Sequential Tool Execution
            tool_outputs = []
            executed_steps = []

            for step in steps:
                step_id = step.get("step_id")
                tool_name = step.get("tool_name")
                tool_params = step.get("tool_params", {})
                description = step.get("description", "")

                run.iterations += 1
                db.commit()

                # Log Tool Call Start
                AgentExecutorService._log_step(
                    db=db,
                    run_id=run.id,
                    org_id=session.organization_id,
                    step_type="tool_call",
                    content=f"Invoking tool '{tool_name}': {description}",
                    metadata={"tool_name": tool_name, "tool_params": tool_params},
                )

                # Check tool permissions
                allowed_list = agent.allowed_tools or []
                if tool_name not in allowed_list:
                    from api.ai.tools import ToolResult
                    res = ToolResult(
                        success=False,
                        tool_name=tool_name,
                        error=f"Permission Denied: Agent is not allowed to use tool '{tool_name}'."
                    )
                else:
                    # Execute Tool
                    res = tool_executor.execute(
                        tool_name=tool_name,
                        params=tool_params,
                        organization_id=str(session.organization_id),
                        user_id=str(session.user_id),
                    )

                tool_outputs.append({
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "success": res.success,
                    "output": res.output,
                    "error": res.error,
                })

                # Log Tool Execution Result
                log_content = (
                    f"Tool '{tool_name}' execution succeeded."
                    if res.success
                    else f"Tool '{tool_name}' failed: {res.error}"
                )
                AgentExecutorService._log_step(
                    db=db,
                    run_id=run.id,
                    org_id=session.organization_id,
                    step_type="tool_result",
                    content=log_content,
                    metadata={"success": res.success, "output": res.output, "error": res.error},
                )

                executed_steps.append({
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "tool_params": tool_params,
                    "success": res.success,
                    "output": res.output,
                })

            run.tool_calls = executed_steps
            db.commit()

            # Step D: Formulate Final LLM Response
            memory_context = MemoryManager.build_memory_context(
                db=db,
                agent_id=agent.id,
                organization_id=session.organization_id,
                session_id=session.id,
            )

            final_prompt_context = (
                f"You are {agent.name}.\n"
                f"Description: {agent.description or ''}\n"
                f"System instruction: {agent.system_prompt or ''}\n\n"
                f"Memory & Guidelines:\n{memory_context}\n\n"
                f"Execution log for this run:\n"
                f"User Request: {user_input}\n"
                f"Your Thought Process: {thought}\n"
                f"Tool Outputs:\n{str(tool_outputs)}\n\n"
                f"Synthesize the outputs and formulate your final response to the user."
            )

            # Call AI Gateway chat interface
            messages_payload = [
                {"role": "system", "content": final_prompt_context},
                {"role": "user", "content": user_input},
            ]

            res_gateway = gateway.chat(
                db=db,
                messages=messages_payload,
                organization_id=session.organization_id,
                user_id=session.user_id,
                model_name=agent.preferred_model,
                temperature=agent.temperature,
            )

            # Save results & update telemetry
            run.agent_output = res_gateway.get("content", "")
            run.total_tokens = (
                res_gateway.get("prompt_tokens", 0) + res_gateway.get("completion_tokens", 0)
            )
            run.latency_ms = int((time.perf_counter() - start_time) * 1000)
            run.status = AgentRunStatus.COMPLETED

            # Log Final Response
            AgentExecutorService._log_step(
                db=db,
                run_id=run.id,
                org_id=session.organization_id,
                step_type="final_answer",
                content="Agent run completed successfully.",
            )

            # Write latest prompt interactions to memory if enabled
            if agent.memory_enabled:
                MemoryManager.write_memory(
                    db=db,
                    agent_id=agent.id,
                    organization_id=session.organization_id,
                    key=f"last_interaction_{int(time.time())}",
                    value=f"User: {user_input}\nAgent: {run.agent_output}",
                    session_id=session.id,
                )

            db.commit()
            return run

        except Exception as e:
            db.rollback()
            run.status = AgentRunStatus.FAILED
            run.error_message = str(e)
            run.latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Log execution failure
            try:
                AgentExecutorService._log_step(
                    db=db,
                    run_id=run.id,
                    org_id=session.organization_id,
                    step_type="final_answer",
                    content=f"Agent execution failed: {str(e)}",
                    level="ERROR",
                )
            except Exception:
                pass

            db.commit()
            return run

    @staticmethod
    def _log_step(
        db: Session,
        run_id: uuid.UUID,
        org_id: uuid.UUID,
        step_type: str,
        content: str,
        level: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        log = AgentLog(
            run_id=run_id,
            organization_id=org_id,
            level=level,
            step_type=step_type,
            content=content,
            meta_data=metadata,
        )
        db.add(log)
        db.commit()
