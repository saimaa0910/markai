"""
Agent Runtime — Sprint 7.1
===========================
Central Agent Runtime coordinator.

Lifecycle:
  1. Load AgentDefinition
  2. Load Prompt (Prompt Platform)
  3. Build Context (ContextBuilder)
  4. Select Model (via agent config → AIGateway)
  5. Execute Plan (AgentPlannerService → ToolExecutor)
  6. Call AIGateway for final response
  7. Reflect (AIReflector)
  8. Evaluate (AIEvaluator → persist agent_evaluations)
  9. Persist Run (AgentRun update)
  10. Write Memory (MemoryManager)
  11. Return structured result

All sub-systems are REUSED from existing services.
No gateway, provider, router, or memory duplication.
"""
import uuid
import time
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentRunStatus
from api.repositories.agent import agent_run_repo, agent_log_repo
from api.services.agent_planner import AgentPlannerService
from api.services.memory_manager import MemoryManager
from api.ai.tools.registry import ToolExecutor
from api.ai.gateway.coordinator import AIGateway
from api.ai.context.builder import build_agent_context
from api.ai.reflection.reflection import ai_reflector
from api.ai.evaluation.evaluator import ai_evaluator

logger = logging.getLogger(__name__)


class AgentRunResult:
    """Structured result returned by the Agent Runtime."""

    def __init__(
        self,
        run: AgentRun,
        evaluation: Optional[Any] = None,
        reflection: Optional[Any] = None,
        context: str = "",
    ) -> None:
        self.run = run
        self.evaluation = evaluation
        self.reflection = reflection
        self.context = context

    @property
    def success(self) -> bool:
        return self.run.status == AgentRunStatus.COMPLETED


class AgentRuntime:
    """
    Production-grade Agent Runtime coordinator.
    Orchestrates all Sprint 7.1 components in the correct order.
    """

    def __init__(self) -> None:
        self.gateway = AIGateway()

    def execute(
        self,
        db: Session,
        session: AgentSession,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> AgentRunResult:
        """
        Execute a full agent run lifecycle.
        Equivalent to AgentExecutorService.run_agent_session() but extended
        with Context Builder, Reflection, and Evaluation.
        """
        start_time = time.perf_counter()
        agent: AgentDefinition = session.agent

        # --- Create Run Record ---
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
        cost_usd = 0.0

        try:
            # --- Step 1: Log start ---
            self._log(db, run.id, session.organization_id, "thought", "Building execution context...")

            # --- Step 2: Build Context ---
            context_str = build_agent_context(
                db=db,
                agent=agent,
                user_input=user_input,
                session_id=session.id,
                user_id=session.user_id,
                organization_id=session.organization_id,
                conversation_history=conversation_history or [],
            )

            # --- Step 3: Generate Plan ---
            self._log(db, run.id, session.organization_id, "thought", "Generating execution plan...")
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

            thought = plan.get("thought", "Processing your request...")
            steps = plan.get("steps", [])
            self._log(db, run.id, session.organization_id, "thought", thought, metadata={"plan": plan})

            # --- Step 4: Execute Tools ---
            tool_outputs: List[Dict[str, Any]] = []
            for step in steps:
                step_id = step.get("step_id")
                tool_name = step.get("tool_name")
                tool_params = step.get("tool_params", {})
                description = step.get("description", "")

                run.iterations += 1
                db.commit()

                self._log(
                    db, run.id, session.organization_id, "tool_call",
                    f"Invoking tool '{tool_name}': {description}",
                    metadata={"tool_name": tool_name, "tool_params": tool_params},
                )

                allowed_list = agent.allowed_tools or []
                if tool_name not in allowed_list:
                    from api.ai.tools import ToolResult
                    res = ToolResult(
                        success=False,
                        tool_name=tool_name,
                        error=f"Permission denied: agent not allowed to use '{tool_name}'.",
                    )
                else:
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

                log_content = (
                    f"Tool '{tool_name}' succeeded."
                    if res.success
                    else f"Tool '{tool_name}' failed: {res.error}"
                )
                self._log(
                    db, run.id, session.organization_id, "tool_result", log_content,
                    metadata={"success": res.success, "output": res.output, "error": res.error},
                )

            run.tool_calls = tool_outputs
            db.commit()

            # --- Step 5: Build Final Prompt with Context Builder ---
            final_context = build_agent_context(
                db=db,
                agent=agent,
                user_input=user_input,
                session_id=session.id,
                user_id=session.user_id,
                organization_id=session.organization_id,
                tool_results=tool_outputs,
                conversation_history=conversation_history or [],
            )

            messages_payload = [
                {"role": "system", "content": final_context},
                {"role": "user", "content": user_input},
            ]

            # --- Step 6: Call Gateway ---
            self._log(db, run.id, session.organization_id, "thought", "Synthesizing final response...")
            gateway_result = self.gateway.chat(
                db=db,
                messages=messages_payload,
                organization_id=session.organization_id,
                user_id=session.user_id,
                model_name=agent.preferred_model,
                temperature=agent.temperature,
            )

            agent_output = gateway_result.get("content", "")
            prompt_tokens = gateway_result.get("prompt_tokens", 0)
            completion_tokens = gateway_result.get("completion_tokens", 0)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            run.agent_output = agent_output
            run.total_tokens = prompt_tokens + completion_tokens
            run.latency_ms = latency_ms
            run.status = AgentRunStatus.COMPLETED

            # --- Step 7: Reflection ---
            reflection_result = None
            if run_reflection:
                try:
                    reflection_result = ai_reflector.evaluate_output(
                        db=db,
                        original_prompt=user_input,
                        generated_output=agent_output,
                        organization_id=session.organization_id,
                        user_id=session.user_id,
                        agent_type=agent.agent_type.value,
                        model_name=agent.preferred_model,
                    )
                except Exception as e:
                    logger.warning("Reflection failed (non-fatal): %s", e)

            # --- Step 8: Evaluation ---
            evaluation_result = None
            if run_evaluation:
                try:
                    evaluation_result = ai_evaluator.evaluate_run(
                        db=db,
                        run_id=run.id,
                        organization_id=session.organization_id,
                        user_id=session.user_id,
                        agent_output=agent_output,
                        user_input=user_input,
                        plan=plan,
                        tool_calls=tool_outputs,
                        total_tokens=run.total_tokens,
                        latency_ms=latency_ms,
                        cost_usd=cost_usd,
                        agent_type=agent.agent_type.value,
                        model_name=agent.preferred_model,
                    )
                except Exception as e:
                    logger.warning("Evaluation failed (non-fatal): %s", e)

            self._log(db, run.id, session.organization_id, "final_answer", "Agent run completed successfully.")

            # --- Step 9: Persist Memory ---
            if agent.memory_enabled:
                MemoryManager.write_memory(
                    db=db,
                    agent_id=agent.id,
                    organization_id=session.organization_id,
                    key=f"last_interaction_{int(time.time())}",
                    value=f"User: {user_input}\nAgent: {agent_output}",
                    session_id=session.id,
                )

            db.commit()
            return AgentRunResult(
                run=run,
                evaluation=evaluation_result,
                reflection=reflection_result,
                context=context_str,
            )

        except Exception as e:
            logger.error("AgentRuntime execution error: %s", e)
            db.rollback()
            run.status = AgentRunStatus.FAILED
            run.error_message = str(e)
            run.latency_ms = int((time.perf_counter() - start_time) * 1000)
            try:
                self._log(
                    db, run.id, session.organization_id, "final_answer",
                    f"Agent run failed: {str(e)}", level="ERROR",
                )
            except Exception:
                pass
            db.commit()
            return AgentRunResult(run=run)

    @staticmethod
    def _log(
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


# Module-level singleton
agent_runtime = AgentRuntime()
