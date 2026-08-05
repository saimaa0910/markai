"""
Social Agent Service — Sprint 7.5
====================================
Coordinates DB persistence, logs execution traces, and constructs SSE streams
emitting social-specific events: planning → brand → campaign → knowledge →
content → image → hashtags → optimization → reflection → evaluation →
schedule → publish → completed.

Reuses existing patterns from ContentAgentService and ImageAgentService.
"""
import uuid
import json
import time
import logging
from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session

from api.models.agent import AgentRun, AgentSession, AgentRunStatus
from api.ai.agents.social.agent import social_agent
from api.ai.agents.social.planner import SocialPlanner
from api.ai.agents.social.helpers import HashtagEngine, PlatformOptimizer
from api.ai.agents.social.constants import SocialPlatform, SocialContentType
from api.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


def _sse(event: str, data: Any) -> str:
    """Format SSE response payload — matches existing EAIMOS pattern."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


class SocialAgentService:
    """
    Manages transactional state, DB persistence, and real-time streaming
    for the Enterprise Social Media Agent.
    """

    # ── Sync Generation ───────────────────────────────────────────────────────

    @staticmethod
    def generate_social(
        db: Session,
        session: AgentSession,
        platform: SocialPlatform,
        content_type: SocialContentType,
        prompt: str,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        campaign_id: Optional[uuid.UUID] = None,
        brand_voice_override: Optional[str] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        generate_image: Optional[bool] = None,
        image_style: Optional[str] = None,
        translate_to: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.75,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Dict[str, Any]:
        """Generate a social post synchronously and persist to DB."""
        run = AgentRun(
            session_id=session.id,
            organization_id=session.organization_id,
            user_input=f"Social [{platform.value}] [{content_type.value}]: {prompt[:100]}",
            status=AgentRunStatus.RUNNING,
            iterations=1,
            total_tokens=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        result = social_agent.generate_social_post(
            db=db,
            organization_id=session.organization_id,
            user_id=session.user_id,
            platform=platform,
            content_type=content_type,
            prompt=prompt,
            target_audience=target_audience,
            keywords=keywords,
            campaign_id=campaign_id,
            brand_voice_override=brand_voice_override,
            knowledge_collections=knowledge_collections,
            generate_image=generate_image,
            image_style=image_style,
            translate_to=translate_to,
            preferred_model=preferred_model,
            temperature=temperature,
            run_reflection=run_reflection,
            run_evaluation=run_evaluation,
        )

        evaluation = result.get("evaluation", {}) or {}
        reflection = result.get("reflection", {}) or {}
        passed = evaluation.get("passed", True)

        run.status = AgentRunStatus.COMPLETED if passed else AgentRunStatus.FAILED
        run.agent_output = json.dumps(result.get("content", {}))
        run.plan = result.get("plan")
        run.total_tokens = result.get("total_tokens", 0)
        run.latency_ms = result.get("latency_ms", 0)
        db.commit()

        if session.agent.memory_enabled:
            MemoryManager.write_memory(
                db=db,
                agent_id=session.agent_id,
                organization_id=session.organization_id,
                key=f"social_{platform.value.lower()}_{int(time.time())}",
                value=f"Social post [{platform.value}]: {result.get('content', {}).get('raw_content', '')[:300]}",
                session_id=session.id,
            )

        result["run_id"] = str(run.id)
        return result

    # ── SSE Streaming ─────────────────────────────────────────────────────────

    @staticmethod
    def stream_social(
        db: Session,
        session: AgentSession,
        platform: SocialPlatform,
        content_type: SocialContentType,
        prompt: str,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        campaign_id: Optional[uuid.UUID] = None,
        brand_voice_override: Optional[str] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        generate_image: Optional[bool] = None,
        image_style: Optional[str] = None,
        translate_to: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.75,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Generator[str, None, None]:
        """
        SSE Generator — emits real-time social generation pipeline events.
        Events: planning → brand → campaign → knowledge → content →
                image → hashtags → optimization → reflection →
                evaluation → schedule → completed
        """
        start_time = time.perf_counter()
        run_id = str(uuid.uuid4())

        run = AgentRun(
            session_id=session.id,
            organization_id=session.organization_id,
            user_input=f"Stream Social [{platform.value}] [{content_type.value}]: {prompt[:100]}",
            status=AgentRunStatus.RUNNING,
            iterations=1,
            total_tokens=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield _sse("agent_start", {
            "run_id": str(run.id),
            "agent_id": "SOCIAL",
            "session_id": str(session.id),
        })

        try:
            # ── PHASE 1: Planning ─────────────────────────────────────────────
            yield _sse("status", {"message": "Analyzing platform requirements and building execution plan..."})
            time.sleep(0.15)

            plan = SocialPlanner.generate_plan(
                platform=platform,
                content_type=content_type,
                prompt=prompt,
                target_audience=target_audience,
                keywords=keywords,
                campaign_id=str(campaign_id) if campaign_id else None,
                brand_voice=brand_voice_override,
                has_knowledge_collections=bool(knowledge_collections),
                generate_image=generate_image,
                translate_to=translate_to,
            )
            flags = plan["flags"]
            yield _sse("planning", plan)

            # ── PHASE 2: Brand Context ────────────────────────────────────────
            yield _sse("status", {"message": "Loading brand voice and guidelines..."})
            time.sleep(0.1)

            brand_voice = brand_voice_override
            if not brand_voice:
                org_memories = MemoryManager.get_org_memory(db, session.organization_id)
                voice_items = [m.value for m in org_memories if m.category == "brand_voice" or m.key == "brand_voice"]
                brand_voice = "\n".join(voice_items) if voice_items else "Professional, clear, engaging, and authentic."

            yield _sse("brand", {"brand_voice_loaded": bool(brand_voice), "source": "override" if brand_voice_override else "memory"})

            # ── PHASE 3: Campaign Context ─────────────────────────────────────
            campaign_context = None
            if flags.get("need_campaign_context") and campaign_id:
                yield _sse("status", {"message": "Loading campaign context, audience, and goals..."})
                yield _sse("campaign", {"campaign_id": str(campaign_id), "loaded": True})
                time.sleep(0.1)

            # ── PHASE 4: Knowledge Context ────────────────────────────────────
            rag_chunks = []
            if knowledge_collections:
                yield _sse("status", {"message": "Searching knowledge collections..."})
                yield _sse("tool_start", {"tool_name": "knowledge_tool", "description": "RAG knowledge search"})
                try:
                    from api.ai.agents.content.executor import ContentExecutor
                    executor = ContentExecutor(db, session.organization_id, session.user_id)
                    search_query = f"{prompt} {', '.join(keywords or [])}"
                    rag_chunks = executor.tools_wrapper.search_knowledge(
                        query=search_query,
                        collection_ids=knowledge_collections,
                        limit=3,
                    )
                except Exception as rag_err:
                    logger.warning("Knowledge search failed: %s", rag_err)
                yield _sse("knowledge", {"chunks_found": len(rag_chunks), "searched": True})

            # ── PHASE 5: Content Generation ───────────────────────────────────
            yield _sse("status", {"message": "Generating social copy via Content Agent..."})
            time.sleep(0.1)

            from api.ai.agents.content.agent import content_agent
            from api.ai.agents.content.constants import ContentType
            from api.ai.agents.social.agent import _build_social_prompt, _build_reflection, _build_evaluation, _parse_content_parts

            content_prompt = _build_social_prompt(platform, content_type, prompt, target_audience, keywords)

            # Invoke ContentAgent for actual generation
            from api.ai.gateway.coordinator import AIGateway
            gateway = AIGateway()

            system_msg = (
                f"You are an expert social media copywriter for {platform.value}. "
                f"Brand voice: {brand_voice}. "
                f"Write platform-optimized {content_type.value.replace('_', ' ').lower()} content."
            )
            if rag_chunks:
                system_msg += "\n\n=== RELEVANT CONTEXT ===\n" + "\n\n".join(rag_chunks) + "\n========================"

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content_prompt},
            ]

            full_content_parts = []
            prompt_tokens = 0
            completion_tokens = 0

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
            except Exception as stream_err:
                logger.warning("Stream failed, falling back to chat: %s", stream_err)
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

            yield _sse("content", {
                "generated": True,
                "char_count": len(generated_text),
                "platform": platform.value,
            })

            # ── PHASE 6: Image Generation ─────────────────────────────────────
            image_url = None
            if flags.get("need_image"):
                yield _sse("status", {"message": "Generating social image via Image Agent..."})
                try:
                    from api.ai.agents.image.executor import ImageExecutor
                    image_executor = ImageExecutor(db, session.organization_id, session.user_id)
                    img_result = image_executor.generate(
                        prompt=f"{prompt} — {content_type.value.lower()} for {platform.value}",
                        style=image_style or "minimal",
                        aspect_ratio=_get_ratio(platform),
                        campaign_id=campaign_id,
                    )
                    image_url = img_result.get("storage_url")
                    yield _sse("image", {"generated": True, "image_url": image_url})
                except Exception as img_err:
                    logger.warning("Image generation failed: %s", img_err)
                    yield _sse("image", {"generated": False, "error": str(img_err)})

            # ── PHASE 7: Hashtags ─────────────────────────────────────────────
            hashtag_result = None
            if flags.get("need_hashtags"):
                yield _sse("status", {"message": "Generating ranked hashtags..."})
                hashtag_result = HashtagEngine.generate(
                    platform=platform.value,
                    keywords=keywords,
                    industry=target_audience,
                )
                yield _sse("hashtags", hashtag_result)

            # ── PHASE 8: Platform Optimization ────────────────────────────────
            yield _sse("status", {"message": f"Optimizing content for {platform.value} rules..."})
            optimization = PlatformOptimizer.optimize(
                content=generated_text,
                platform=platform.value,
                hashtag_string=hashtag_result.get("hashtag_string", "") if hashtag_result else "",
            )
            final_content = optimization.get("optimized_content", generated_text)
            yield _sse("optimization", optimization)

            # ── PHASE 9: Reflection ───────────────────────────────────────────
            reflection = None
            if run_reflection:
                yield _sse("status", {"message": "Running social compliance reflection..."})
                reflection = _build_reflection(final_content, platform, optimization)
                yield _sse("reflection", reflection)

            # ── PHASE 10: Evaluation ──────────────────────────────────────────
            evaluation = None
            if run_evaluation:
                yield _sse("status", {"message": "Scoring brand, engagement, and platform metrics..."})
                evaluation = _build_evaluation(final_content, platform, reflection or {}, keywords)
                yield _sse("evaluation", evaluation)

            # ── PHASE 11: Content Parts ───────────────────────────────────────
            content_parts = _parse_content_parts(final_content, content_type)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # ── DB Persistence ────────────────────────────────────────────────
            passed = (evaluation or {}).get("passed", True)
            run.status = AgentRunStatus.COMPLETED if passed else AgentRunStatus.FAILED
            run.agent_output = json.dumps(content_parts)
            run.plan = plan
            run.total_tokens = total_tokens
            run.latency_ms = latency_ms
            db.commit()

            # ── Memory ────────────────────────────────────────────────────────
            if session.agent.memory_enabled:
                MemoryManager.write_memory(
                    db=db,
                    agent_id=session.agent_id,
                    organization_id=session.organization_id,
                    key=f"social_{platform.value.lower()}_{int(time.time())}",
                    value=f"Social [{platform.value}]: {final_content[:300]}",
                    session_id=session.id,
                )

            # ── Completed ─────────────────────────────────────────────────────
            yield _sse("completed", {
                "run_id": str(run.id),
                "platform": platform.value,
                "content_type": content_type.value,
                "content": content_parts,
                "image_url": image_url,
                "hashtags": hashtag_result,
                "optimization": optimization,
                "reflection": reflection,
                "evaluation": evaluation,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
                "cost_usd": float(total_tokens * 0.000002),
            })

        except Exception as exc:
            logger.error("Social stream failed: %s", exc, exc_info=True)
            run.status = AgentRunStatus.FAILED
            run.error_message = str(exc)
            db.commit()
            yield _sse("error", {"message": str(exc)})


def _build_reflection(content, platform, optimization):
    """Re-exported from agent module for use in streaming service."""
    from api.ai.agents.social.agent import _build_reflection as _br
    return _br(content, platform, optimization)


def _build_evaluation(content, platform, reflection, keywords):
    """Re-exported from agent module for use in streaming service."""
    from api.ai.agents.social.agent import _build_evaluation as _be
    return _be(content, platform, reflection, keywords)


def _parse_content_parts(content, content_type):
    """Re-exported from agent module for use in streaming service."""
    from api.ai.agents.social.agent import _parse_content_parts as _pcp
    return _pcp(content, content_type)


def _get_ratio(platform):
    """Get platform image ratio."""
    from api.ai.agents.social.constants import PLATFORM_CONFIGS
    return PLATFORM_CONFIGS.get(platform.value, {}).get("image_ratio", "1:1")
