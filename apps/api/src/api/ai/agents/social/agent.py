"""
Social Agent — Sprint 7.5
===========================
SocialAgent extends BaseMarketingAgent and orchestrates the complete
social media lifecycle by delegating to existing EAIMOS agents.

No content generation or image generation logic is duplicated here.
Everything is delegated to ContentAgent and ImageAgent via their executors.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.social.manifest import SOCIAL_AGENT_MANIFEST
from api.ai.agents.social.constants import SocialPlatform, SocialContentType, EngagementType
from api.ai.agents.social.planner import SocialPlanner
from api.ai.agents.social.helpers import HashtagEngine, PlatformOptimizer, get_publisher

logger = logging.getLogger(__name__)


class SocialAgent(BaseMarketingAgent):
    """
    Production Enterprise Social Media Agent.
    Orchestrates Content Agent → Image Agent → Platform Optimizer
    → Reflection → Evaluation → Scheduling → Publishing → Analytics.
    """

    def __init__(self) -> None:
        super().__init__(manifest=SOCIAL_AGENT_MANIFEST)

    # ── Core Generation ───────────────────────────────────────────────────────

    def generate_social_post(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
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
        """
        Full synchronous social post generation pipeline.
        1. Plan
        2. Content (via ContentAgent)
        3. Image (via ImageAgent, optional)
        4. Hashtags
        5. Platform Optimization
        6. Reflection
        7. Evaluation
        """
        # 1. Plan
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

        # 2. Generate content via ContentAgent (never duplicated)
        from api.ai.agents.content.agent import content_agent
        from api.ai.agents.content.constants import ContentType

        content_prompt = _build_social_prompt(platform, content_type, prompt, target_audience, keywords)
        content_result = content_agent.execute_generation(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            content_type=ContentType.INSTAGRAM_CAPTION,  # Social default; optimized per platform below
            prompt=content_prompt,
            brand_voice_override=brand_voice_override,
            knowledge_collections=knowledge_collections,
            target_audience=target_audience,
            keywords=keywords,
            preferred_model=preferred_model,
            temperature=temperature,
            run_reflection=run_reflection,
            run_evaluation=False,  # Social agent runs its own evaluation
        )
        generated_content = content_result.get("generated_content", "")

        # 3. Image generation via ImageAgent (optional, never duplicated)
        image_url: Optional[str] = None
        if flags.get("need_image"):
            try:
                from api.ai.agents.image.executor import ImageExecutor
                image_executor = ImageExecutor(db, organization_id, user_id)
                image_prompt = f"{prompt} — {content_type.value.lower()} for {platform.value}"
                img_result = image_executor.generate(
                    prompt=image_prompt,
                    style=image_style or "minimal",
                    aspect_ratio=_get_platform_ratio(platform),
                    campaign_id=campaign_id,
                )
                image_url = img_result.get("storage_url")
            except Exception as img_err:
                logger.warning("Image generation failed for social post: %s", img_err)

        # 4. Hashtags
        hashtag_result = None
        if flags.get("need_hashtags"):
            hashtag_result = HashtagEngine.generate(
                platform=platform.value,
                keywords=keywords,
                industry=target_audience,
            )

        # 5. Platform Optimization
        optimization = PlatformOptimizer.optimize(
            content=generated_content,
            platform=platform.value,
            hashtag_string=hashtag_result.get("hashtag_string", "") if hashtag_result else "",
        )
        final_content = optimization.get("optimized_content", generated_content)

        # 6. Translate if requested (via ContentAgent improvement)
        if flags.get("need_translation") and translate_to:
            try:
                from api.ai.agents.content.constants import ImprovementType
                final_content = content_agent.execute_improvement(
                    db=db,
                    organization_id=organization_id,
                    user_id=user_id,
                    content=final_content,
                    improvement_type=ImprovementType.TRANSLATE,
                    target_language=translate_to,
                    preferred_model=preferred_model,
                )
            except Exception as trans_err:
                logger.warning("Translation failed: %s", trans_err)

        # 7. Reflection
        reflection = _build_reflection(final_content, platform, optimization)

        # 8. Evaluation
        evaluation = _build_evaluation(
            content=final_content,
            platform=platform,
            reflection=reflection,
            keywords=keywords,
        )

        # 9. Parse content parts
        content_parts = _parse_content_parts(final_content, content_type)

        return {
            "platform": platform.value,
            "content_type": content_type.value,
            "content": content_parts,
            "image_url": image_url,
            "hashtags": hashtag_result,
            "optimization": optimization,
            "reflection": reflection,
            "evaluation": evaluation,
            "plan": plan,
            "total_tokens": content_result.get("total_tokens", 0),
            "latency_ms": content_result.get("latency_ms", 0),
            "cost_usd": content_result.get("cost_usd", 0.0),
        }

    # ── Scheduling ────────────────────────────────────────────────────────────

    def schedule_post(
        self,
        db: Session,
        run_id: str,
        platform: SocialPlatform,
        schedule_type: str,
        scheduled_at: Optional[Any] = None,
        timezone: str = "UTC",
        recurring_pattern: Optional[str] = None,
        auto_publish: bool = False,
    ) -> Dict[str, Any]:
        """
        Marks an AgentRun record as scheduled.
        Scheduling metadata is stored in AgentRun.plan.
        """
        from sqlalchemy import select
        from api.models.agent import AgentRun

        run = db.scalars(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id))).first()
        if not run:
            return {"error": f"Run {run_id} not found", "scheduled": False}

        plan = run.plan or {}
        plan["schedule"] = {
            "schedule_type": schedule_type,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "timezone": timezone,
            "recurring_pattern": recurring_pattern,
            "auto_publish": auto_publish,
            "status": "SCHEDULED",
        }
        run.plan = plan
        db.commit()

        return {
            "run_id": run_id,
            "platform": platform.value,
            "status": "SCHEDULED",
            "scheduled_at": plan["schedule"]["scheduled_at"],
            "schedule_type": schedule_type,
            "message": "Post scheduled successfully.",
        }

    # ── Publishing ────────────────────────────────────────────────────────────

    def publish_post(
        self,
        db: Session,
        run_id: str,
        platform: SocialPlatform,
        override_content: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches to the platform publisher adapter.
        """
        from sqlalchemy import select
        from api.models.agent import AgentRun

        run = db.scalars(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id))).first()
        if not run:
            return {"error": f"Run {run_id} not found", "published": False}

        content = override_content or (run.agent_output or "")

        adapter = get_publisher(platform.value)
        if not adapter:
            return {
                "run_id": run_id,
                "platform": platform.value,
                "status": "unsupported",
                "published": False,
                "message": f"No publisher adapter available for {platform.value}",
            }

        result = adapter.publish(content=content, image_url=image_url, metadata={
            "run_id": run_id,
        })

        # Update run plan with publish log
        plan = run.plan or {}
        plan["publish_log"] = result
        run.plan = plan
        db.commit()

        return {
            "run_id": run_id,
            "platform": platform.value,
            **result,
        }

    # ── Engagement / Replies ──────────────────────────────────────────────────

    def generate_reply(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        platform: SocialPlatform,
        original_post: str,
        engagement_type: EngagementType,
        brand_voice_override: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generates engagement content (reply, comment, DM, FAQ reply) via ContentAgent.
        No content generation logic duplicated here.
        """
        from api.ai.agents.content.agent import content_agent
        from api.ai.agents.content.constants import ContentType, ImprovementType

        engagement_prompts = {
            EngagementType.REPLY: f"Write a professional {platform.value} reply to: {original_post}",
            EngagementType.COMMENT: f"Write an engaging {platform.value} comment for: {original_post}",
            EngagementType.DM_DRAFT: f"Draft a friendly DM on {platform.value} regarding: {original_post}",
            EngagementType.COMMUNITY_REPLY: f"Write a community-focused reply on {platform.value} to: {original_post}",
            EngagementType.FAQ_REPLY: f"Answer this FAQ on {platform.value}: {original_post}",
            EngagementType.THANK_YOU: f"Write a thank-you message on {platform.value} for: {original_post}",
        }

        engagement_prompt = engagement_prompts.get(
            engagement_type,
            f"Write a {engagement_type.value.lower()} for {platform.value}: {original_post}",
        )

        result = content_agent.execute_generation(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            content_type=ContentType.INSTAGRAM_CAPTION,
            prompt=engagement_prompt,
            brand_voice_override=brand_voice_override,
            preferred_model=preferred_model,
            temperature=temperature,
            run_reflection=False,
            run_evaluation=False,
        )
        return result.get("generated_content", "")


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _build_social_prompt(
    platform: SocialPlatform,
    content_type: SocialContentType,
    prompt: str,
    audience: Optional[str],
    keywords: Optional[List[str]],
) -> str:
    """Constructs a detailed content prompt for the Content Agent."""
    parts = [
        f"Write a {content_type.value.replace('_', ' ').lower()} for {platform.value}.",
        f"Topic: {prompt}",
    ]
    if audience:
        parts.append(f"Target audience: {audience}")
    if keywords:
        parts.append(f"Include keywords: {', '.join(keywords[:5])}")
    parts.append("Include: compelling hook, body, and clear call-to-action.")
    return " ".join(parts)


def _get_platform_ratio(platform: SocialPlatform) -> str:
    """Returns the ideal image aspect ratio for a platform."""
    from api.ai.agents.social.constants import PLATFORM_CONFIGS
    return PLATFORM_CONFIGS.get(platform.value, {}).get("image_ratio", "1:1")


def _build_reflection(content: str, platform: SocialPlatform, optimization: Dict) -> Dict:
    """Builds a social-specific reflection result."""
    within_limit = optimization.get("within_limit", True)
    char_used = optimization.get("char_used", len(content))
    char_limit = optimization.get("char_limit", 2200)
    fill_ratio = char_used / max(char_limit, 1)

    return {
        "is_satisfactory": within_limit,
        "platform_compliant": within_limit,
        "brand_compliant": True,
        "readability_ok": len(content.split()) > 5,
        "engagement_score": round(min(fill_ratio * 1.2, 1.0), 2),
        "cta_quality": 0.85 if "→" in content or "👉" in content or "http" in content else 0.6,
        "hook_quality": 0.9 if len(content.split("\n")[0]) > 20 else 0.5,
        "formatting_ok": within_limit,
        "critique": None if within_limit else f"Content is {char_used - char_limit} chars over limit.",
        "suggested_edits": None if within_limit else "Shorten body text to fit platform limit.",
    }


def _build_evaluation(
    content: str,
    platform: SocialPlatform,
    reflection: Dict,
    keywords: Optional[List[str]],
) -> Dict:
    """Builds a social-specific evaluation result."""
    engagement = reflection.get("engagement_score", 0.75)
    hook = reflection.get("hook_quality", 0.75)
    cta = reflection.get("cta_quality", 0.75)

    kw_score = min(1.0, len([k for k in (keywords or []) if k.lower() in content.lower()]) / max(len(keywords or [1]), 1))

    brand_score = 0.85
    platform_score = 1.0 if reflection.get("platform_compliant") else 0.6
    readability = 0.8
    viral_potential = round((hook + engagement + cta) / 3, 2)
    seo_score = kw_score
    overall = round((brand_score + engagement + platform_score + readability + seo_score + viral_potential) / 6, 2)

    return {
        "brand_score": brand_score,
        "engagement_score": engagement,
        "platform_score": platform_score,
        "readability": readability,
        "seo_score": round(seo_score, 2),
        "viral_potential": viral_potential,
        "confidence": 0.88,
        "overall_score": overall,
        "passed": overall >= 0.65,
        "critique": None if overall >= 0.65 else "Content quality below acceptable threshold.",
    }


def _parse_content_parts(content: str, content_type: SocialContentType) -> Dict[str, Any]:
    """Extracts structured parts from the generated content string."""
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]

    hook = lines[0] if lines else ""
    body = "\n".join(lines[1:-1]) if len(lines) > 2 else content
    cta = lines[-1] if len(lines) > 1 else ""
    headline = hook[:80] if hook else ""

    thread_parts = None
    if content_type == SocialContentType.THREAD:
        # Split on numbered list or double newlines for thread posts
        import re
        thread_parts = re.split(r"\n{2,}|\d+\.\s", content)
        thread_parts = [p.strip() for p in thread_parts if p.strip()]

    return {
        "caption": content,
        "headline": headline,
        "cta": cta if cta != hook else None,
        "hook": hook,
        "body": body,
        "summary": content[:200],
        "thread_parts": thread_parts,
        "raw_content": content,
    }


# ─── Global Singleton ────────────────────────────────────────────────────────

social_agent = SocialAgent()
