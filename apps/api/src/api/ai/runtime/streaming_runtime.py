"""
Agent Streaming Runtime — SSE (Server-Sent Events)
====================================================
Provides a streaming generator that yields SSE-formatted events
for the agent execution lifecycle.

Event types emitted:
  - event: agent_start        — run created, metadata
  - event: context_ready      — context built
  - event: plan               — plan generated (thought + steps)
  - event: tool_call          — tool invocation started
  - event: tool_result        — tool execution result
  - event: token              — LLM response token (streaming)
  - event: reflection         — reflection scores
  - event: evaluation         — evaluation scores
  - event: done               — run complete with full output
  - event: error              — error event

Reuses:
  - AIGateway.stream() for token streaming
  - AgentPlannerService for plan generation
  - ToolExecutor for tool dispatch
  - ContextBuilder for prompt assembly
  - MemoryManager for memory I/O
"""
import uuid
import time
import json
import logging
from typing import Optional, Dict, Any, List, Generator
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentRunStatus
from api.services.agent_planner import AgentPlannerService
from api.services.memory_manager import MemoryManager
from api.ai.tools.registry import ToolExecutor
from api.ai.gateway.coordinator import AIGateway
from api.ai.context.builder import build_agent_context
from api.ai.reflection.reflection import ai_reflector
from api.ai.evaluation.evaluator import ai_evaluator

logger = logging.getLogger(__name__)


def _sse(event: str, data: Any) -> str:
    """Format a single SSE message."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


def _sse_error(message: str) -> str:
    return _sse("error", {"message": message})


class AgentStreamingRuntime:
    """
    SSE-compatible streaming runtime for agent execution.
    Yields formatted SSE strings throughout the agent lifecycle.
    """

    def __init__(self) -> None:
        self.gateway = AIGateway()

    def stream_run(
        self,
        db: Session,
        session: AgentSession,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Generator[str, None, None]:
        """
        Execute agent run with SSE streaming.
        Yields SSE-formatted strings that can be returned directly
        from a FastAPI StreamingResponse.
        """
        start_time = time.perf_counter()
        agent: AgentDefinition = session.agent
        tool_executor = ToolExecutor(db)

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

        yield _sse("agent_start", {
            "run_id": str(run.id),
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "session_id": str(session.id),
        })

        try:
            # --- Build Context ---
            yield _sse("status", {"message": "Building execution context..."})
            context_str = build_agent_context(
                db=db,
                agent=agent,
                user_input=user_input,
                session_id=session.id,
                user_id=session.user_id,
                organization_id=session.organization_id,
                conversation_history=conversation_history or [],
            )
            yield _sse("context_ready", {"context_length": len(context_str)})

            # --- Generate Plan ---
            yield _sse("status", {"message": "Generating execution plan..."})
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
            yield _sse("plan", {"thought": thought, "steps": steps, "step_count": len(steps)})

            # --- Execute Tools ---
            tool_outputs: List[Dict[str, Any]] = []
            for step in steps:
                step_id = step.get("step_id", "")
                tool_name = step.get("tool_name", "")
                tool_params = step.get("tool_params", {})
                description = step.get("description", "")

                run.iterations += 1
                db.commit()

                yield _sse("tool_call", {
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "description": description,
                    "params": tool_params,
                })

                allowed_list = agent.allowed_tools or []
                if tool_name not in allowed_list:
                    from api.ai.tools import ToolResult
                    res = ToolResult(
                        success=False,
                        tool_name=tool_name,
                        error=f"Permission denied: '{tool_name}' not in allowed_tools.",
                    )
                else:
                    res = tool_executor.execute(
                        tool_name=tool_name,
                        params=tool_params,
                        organization_id=str(session.organization_id),
                        user_id=str(session.user_id),
                    )

                output_record = {
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "success": res.success,
                    "output": res.output,
                    "error": res.error,
                }
                tool_outputs.append(output_record)

                yield _sse("tool_result", output_record)

            run.tool_calls = tool_outputs
            db.commit()

            # --- Final Context with Tool Results ---
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

            # --- Stream Gateway Response Token by Token ---
            yield _sse("status", {"message": "Generating response..."})
            full_output_parts: List[str] = []
            prompt_tokens = 0
            completion_tokens = 0

            try:
                for chunk in self.gateway.stream(
                    db=db,
                    messages=messages_payload,
                    organization_id=session.organization_id,
                    user_id=session.user_id,
                    model_name=agent.preferred_model,
                    temperature=agent.temperature,
                ):
                    token = chunk.get("content") or chunk.get("token", "")
                    if token:
                        full_output_parts.append(token)
                        yield _sse("token", {"token": token, "run_id": str(run.id)})

                    if chunk.get("done"):
                        prompt_tokens = chunk.get("prompt_tokens", 0)
                        completion_tokens = chunk.get("completion_tokens", 0)

            except Exception as stream_error:
                # Fallback to non-streaming chat if stream unavailable
                logger.warning("Streaming unavailable, falling back to chat: %s", stream_error)
                yield _sse("status", {"message": "Stream unavailable, switching to standard mode..."})
                gateway_result = self.gateway.chat(
                    db=db,
                    messages=messages_payload,
                    organization_id=session.organization_id,
                    user_id=session.user_id,
                    model_name=agent.preferred_model,
                    temperature=agent.temperature,
                )
                fallback_content = gateway_result.get("content", "")
                full_output_parts = [fallback_content]
                prompt_tokens = gateway_result.get("prompt_tokens", 0)
                completion_tokens = gateway_result.get("completion_tokens", 0)
                # Emit all at once as a single token event
                yield _sse("token", {"token": fallback_content, "run_id": str(run.id)})

            agent_output = "".join(full_output_parts)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            run.agent_output = agent_output
            run.total_tokens = prompt_tokens + completion_tokens
            run.latency_ms = latency_ms
            run.status = AgentRunStatus.COMPLETED
            db.commit()

            # --- Reflection ---
            if run_reflection:
                yield _sse("status", {"message": "Running self-reflection..."})
                try:
                    reflection = ai_reflector.evaluate_output(
                        db=db,
                        original_prompt=user_input,
                        generated_output=agent_output,
                        organization_id=session.organization_id,
                        user_id=session.user_id,
                        agent_type=agent.agent_type.value,
                        model_name=agent.preferred_model,
                    )
                    yield _sse("reflection", {
                        "is_satisfactory": reflection.is_satisfactory,
                        "critique": reflection.critique,
                        "scores": reflection.scores.model_dump(),
                    })
                except Exception as e:
                    logger.warning("Reflection failed (non-fatal): %s", e)

            # --- Evaluation ---
            if run_evaluation:
                yield _sse("status", {"message": "Computing evaluation scores..."})
                try:
                    evaluation = ai_evaluator.evaluate_run(
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
                        agent_type=agent.agent_type.value,
                        model_name=agent.preferred_model,
                    )
                    yield _sse("evaluation", evaluation.model_dump())
                except Exception as e:
                    logger.warning("Evaluation failed (non-fatal): %s", e)

            # --- Write Memory ---
            if agent.memory_enabled:
                MemoryManager.write_memory(
                    db=db,
                    agent_id=agent.id,
                    organization_id=session.organization_id,
                    key=f"last_interaction_{int(time.time())}",
                    value=f"User: {user_input}\nAgent: {agent_output}",
                    session_id=session.id,
                )

            # --- Done ---
            yield _sse("done", {
                "run_id": str(run.id),
                "status": "COMPLETED",
                "agent_output": agent_output,
                "total_tokens": run.total_tokens,
                "latency_ms": latency_ms,
                "iterations": run.iterations,
            })

        except Exception as e:
            logger.error("AgentStreamingRuntime error: %s", e)
            try:
                db.rollback()
            except Exception:
                pass
            run.status = AgentRunStatus.FAILED
            run.error_message = str(e)
            run.latency_ms = int((time.perf_counter() - start_time) * 1000)
            try:
                db.commit()
            except Exception:
                pass
            yield _sse_error(str(e))
            yield _sse("done", {
                "run_id": str(run.id),
                "status": "FAILED",
                "error": str(e),
            })


# Module-level singleton
agent_streaming_runtime = AgentStreamingRuntime()
