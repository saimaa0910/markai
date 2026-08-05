"""
Content Agent Service — Sprint 7.2
===================================
Coordinates DB persistence, logs execution traces, and constructs SSE streams
emitting plan steps, tool notifications, token segments, and final metrics.
"""
import uuid
import json
import time
import logging
from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentRunStatus
from api.ai.agents.content.constants import ContentType, ImprovementType
from api.ai.agents.content.agent import content_agent
from api.ai.agents.content.executor import ContentExecutor
from api.ai.agents.content.planner import ContentPlanner
from api.ai.agents.content.reflection import ContentReflector
from api.ai.agents.content.evaluation import ContentEvaluator
from api.ai.agents.content.prompts import get_content_prompt, build_brand_voice_instruction
from api.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


def _sse(event: str, data: Any) -> str:
    """Format string to SSE response payload."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


class ContentAgentService:
    """Manages transactional state, history, and real-time streaming interfaces."""

    @staticmethod
    def generate_content(
        db: Session,
        session: AgentSession,
        content_type: ContentType,
        prompt: str,
        brand_voice_override: Optional[str] = None,
        forbidden_words: Optional[List[str]] = None,
        preferred_words: Optional[List[str]] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Dict[str, Any]:
        """Generate content synchronously and log to DB."""
        # 1. Create a run record
        run = AgentRun(
            session_id=session.id,
            organization_id=session.organization_id,
            user_input=f"Generate {content_type.value}: {prompt[:100]}",
            status=AgentRunStatus.RUNNING,
            iterations=1,
            total_tokens=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 2. Execute Content Agent
        result = content_agent.execute_generation(
            db=db,
            organization_id=session.organization_id,
            user_id=session.user_id,
            content_type=content_type,
            prompt=prompt,
            brand_voice_override=brand_voice_override,
            forbidden_words=forbidden_words,
            preferred_words=preferred_words,
            knowledge_collections=knowledge_collections,
            target_audience=target_audience,
            keywords=keywords,
            preferred_model=preferred_model,
            temperature=temperature,
            run_reflection=run_reflection,
            run_evaluation=run_evaluation,
        )

        # 3. Update Run Record
        run.status = AgentRunStatus.COMPLETED if result.get("reflection_passed", True) else AgentRunStatus.FAILED
        run.agent_output = result.get("generated_content", "")
        run.plan = result.get("plan")
        run.tool_calls = result.get("tool_calls")
        run.total_tokens = result.get("total_tokens", 0)
        run.latency_ms = result.get("latency_ms", 0)
        db.commit()

        # 4. Save to Agent Memory
        if session.agent.memory_enabled:
            MemoryManager.write_memory(
                db=db,
                agent_id=session.agent_id,
                organization_id=session.organization_id,
                key=f"content_{content_type.value.lower()}_{int(time.time())}",
                value=f"Generated {content_type.value}:\n{run.agent_output[:500]}",
                session_id=session.id,
            )

        return result

    @staticmethod
    def stream_generate_content(
        db: Session,
        session: AgentSession,
        content_type: ContentType,
        prompt: str,
        brand_voice_override: Optional[str] = None,
        forbidden_words: Optional[List[str]] = None,
        preferred_words: Optional[List[str]] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Generator[str, None, None]:
        """SSE Generator yielding status, plans, tool executions, streamed tokens, and final evaluation results."""
        start_time = time.perf_counter()
        
        # Create run record
        run = AgentRun(
            session_id=session.id,
            organization_id=session.organization_id,
            user_input=f"Stream Generate {content_type.value}: {prompt[:100]}",
            status=AgentRunStatus.RUNNING,
            iterations=1,
            total_tokens=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield _sse("status", {"message": "Planning content structure..."})
        time.sleep(0.3)

        # Plan
        plan = ContentPlanner.generate_plan(
            content_type=content_type,
            prompt=prompt,
            audience=target_audience,
            keywords=keywords,
            has_collections=bool(knowledge_collections),
        )
        yield _sse("plan", plan)

        # Resolve RAG or guidelines
        brand_voice = brand_voice_override
        if not brand_voice:
            org_memories = MemoryManager.get_org_memory(db, session.organization_id)
            voice_items = [m.value for m in org_memories if m.category == "brand_voice" or m.key == "brand_voice"]
            brand_voice = "\n".join(voice_items) if voice_items else "Professional, clear, engaging."

        rag_chunks = []
        if knowledge_collections:
            yield _sse("status", {"message": "Searching knowledge space..."})
            executor = ContentExecutor(db, session.organization_id, session.user_id)
            yield _sse("tool_start", {"tool_name": "knowledge_tool", "description": " RAG context search"})
            search_query = f"{prompt} {', '.join(keywords or [])}"
            rag_chunks = executor.tools_wrapper.search_knowledge(
                query=search_query,
                collection_ids=knowledge_collections,
                limit=3
            )
            yield _sse("tool_result", {
                "tool_name": "knowledge_tool",
                "success": True,
                "output": {"chunks_found": len(rag_chunks)}
            })

        # Base instructions
        base_prompt = get_content_prompt(
            content_type=content_type,
            prompt=prompt,
            audience=target_audience,
            keywords=keywords,
        )
        
        brand_instruction = build_brand_voice_instruction(
            brand_voice=brand_voice,
            preferred_words=preferred_words,
            forbidden_words=forbidden_words,
        )
        
        system_instruction = "You are a professional Enterprise Content Writer.\n"
        if brand_instruction:
            system_instruction += f"\n{brand_instruction}\n"
        if rag_chunks:
            system_instruction += "\n=== RELEVANT CONTEXT ===\n"
            system_instruction += "\n\n".join(rag_chunks)
            system_instruction += "\n========================\n"

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": base_prompt},
        ]

        yield _sse("status", {"message": "Invoking LLM Writer..."})

        # Stream tokens
        full_content_parts = []
        prompt_tokens = 0
        completion_tokens = 0
        
        from api.ai.gateway.coordinator import AIGateway
        gateway = AIGateway()

        try:
            for chunk in gateway.stream(
                db=db,
                messages=messages,
                organization_id=session.organization_id,
                user_id=session.user_id,
                model_name=preferred_model,
                temperature=temperature,
            ):
                token = chunk.get("token", "")
                if token:
                    full_content_parts.append(token)
                    yield _sse("llm_token", {"token": token})

                if chunk.get("done"):
                    prompt_tokens = chunk.get("prompt_tokens", 0)
                    completion_tokens = chunk.get("completion_tokens", 0)
        except Exception as e:
            # Fallback if streaming is not supported
            logger.warning("Streaming failed, falling back to chat: %s", e)
            res = gateway.chat(
                db=db,
                messages=messages,
                organization_id=session.organization_id,
                user_id=session.user_id,
                model_name=preferred_model,
                temperature=temperature,
            )
            fallback_text = res.get("content", "")
            full_content_parts = [fallback_text]
            yield _sse("llm_token", {"token": fallback_text})

        generated_text = "".join(full_content_parts)
        total_tokens = prompt_tokens + completion_tokens

        # Reflection
        reflection_passed = True
        critique = None
        suggested_edits = None
        
        if run_reflection and generated_text:
            yield _sse("status", {"message": "Running reflection checks..."})
            reflector = ContentReflector()
            generated_text, reflection, attempts = reflector.review_and_correct(
                db=db,
                prompt=prompt,
                content=generated_text,
                organization_id=session.organization_id,
                user_id=session.user_id,
                brand_voice=brand_voice,
                model_name=preferred_model,
            )
            reflection_passed = reflection.is_satisfactory
            critique = reflection.critique
            suggested_edits = reflection.suggested_edits
            
            yield _sse("reflection", {
                "is_satisfactory": reflection_passed,
                "critique": critique,
                "suggested_edits": suggested_edits
            })

        # Evaluation
        seo_metrics = None
        if run_evaluation and generated_text:
            yield _sse("status", {"message": "Running readability & SEO metrics..."})
            seo_metrics = ContentEvaluator.evaluate_seo(
                content=generated_text,
                keywords=keywords,
                title=prompt[:40],
                meta_desc=prompt[:120],
            )
            yield _sse("evaluation", seo_metrics.model_dump())

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Update run DB record
        run.status = AgentRunStatus.COMPLETED if reflection_passed else AgentRunStatus.FAILED
        run.agent_output = generated_text
        run.plan = plan
        run.tool_calls = plan.get("steps", [])
        run.total_tokens = total_tokens
        run.latency_ms = latency_ms
        db.commit()

        # Save memory
        if session.agent.memory_enabled:
            MemoryManager.write_memory(
                db=db,
                agent_id=session.agent_id,
                organization_id=session.organization_id,
                key=f"content_{content_type.value.lower()}_{int(time.time())}",
                value=f"Generated {content_type.value}:\n{generated_text[:500]}",
                session_id=session.id,
            )

        # Send completed message
        yield _sse("completed", {
            "title": prompt[:60],
            "generated_content": generated_text,
            "latency_ms": latency_ms,
            "total_tokens": total_tokens,
            "cost_usd": float(total_tokens * 0.000002),
            "reflection_passed": reflection_passed,
            "overall_score": seo_metrics.seo_score if seo_metrics else 1.0,
        })
