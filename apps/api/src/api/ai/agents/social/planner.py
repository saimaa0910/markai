"""
Social Agent Planner — Sprint 7.5
====================================
Analyzes social media goals and platform requirements to produce a structured
execution plan. Determines exactly which capabilities are needed per request.
"""
from typing import Dict, Any, List, Optional
from api.ai.agents.social.constants import SocialPlatform, SocialContentType, PLATFORM_CONFIGS


class SocialPlanner:
    """
    Produces a step-by-step social execution plan from inputs.
    Decides capability flags before execution begins.
    """

    @staticmethod
    def generate_plan(
        platform: SocialPlatform,
        content_type: SocialContentType,
        prompt: str,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
        brand_voice: Optional[str] = None,
        has_knowledge_collections: bool = False,
        schedule_type: Optional[str] = None,
        generate_image: Optional[bool] = None,
        translate_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a structured execution plan with capability flags.
        Every flag controls whether a downstream module is invoked.
        """
        platform_cfg = PLATFORM_CONFIGS.get(platform.value, {})
        audience = target_audience or "General Audience"
        kw_list = keywords or []

        # ── Decide capability flags ───────────────────────────────────────────

        need_image = (
            generate_image
            if generate_image is not None
            else platform_cfg.get("supports_images", True)
            and content_type not in (SocialContentType.THREAD, SocialContentType.POLL, SocialContentType.QUESTION)
        )

        need_carousel = (
            content_type == SocialContentType.CAROUSEL
            and platform_cfg.get("supports_carousel", False)
        )

        need_cta = content_type in (
            SocialContentType.LAUNCH_POST,
            SocialContentType.PRODUCT_UPDATE,
            SocialContentType.NEWSLETTER_PROMO,
            SocialContentType.EVENT_PROMO,
            SocialContentType.BLOG_PROMO,
            SocialContentType.POST,
            SocialContentType.ANNOUNCEMENT,
        )

        need_hashtags = platform in (
            SocialPlatform.INSTAGRAM,
            SocialPlatform.TWITTER,
            SocialPlatform.LINKEDIN,
            SocialPlatform.THREADS,
            SocialPlatform.FACEBOOK,
            SocialPlatform.PINTEREST,
            SocialPlatform.TIKTOK,
        )

        need_emoji = platform_cfg.get("emoji_friendly", False)

        need_thread = content_type == SocialContentType.THREAD or (
            platform == SocialPlatform.TWITTER
            and content_type in (SocialContentType.CASE_STUDY, SocialContentType.EDUCATIONAL)
        )

        need_seo_keywords = (
            bool(kw_list)
            or platform in (SocialPlatform.YOUTUBE_COMMUNITY, SocialPlatform.MEDIUM, SocialPlatform.QUORA)
        )

        need_translation = bool(translate_to)

        need_scheduling = schedule_type and schedule_type != "PUBLISH_NOW"

        need_campaign_context = bool(campaign_id)

        need_analytics_context = content_type in (
            SocialContentType.POST,
            SocialContentType.LAUNCH_POST,
            SocialContentType.PRODUCT_UPDATE,
        )

        need_workflow_automation = need_scheduling

        # ── Build thought string ──────────────────────────────────────────────

        thought = (
            f"Planning '{content_type.value}' for {platform.value} targeting '{audience}'. "
            f"Topic: '{prompt[:120]}'. "
        )
        if kw_list:
            thought += f"SEO keywords: {', '.join(kw_list[:5])}. "
        if campaign_id:
            thought += f"Linked to campaign context. "
        if need_image:
            thought += "Image generation is required. "
        if need_thread:
            thought += "Thread format required. "
        if translate_to:
            thought += f"Translating output to {translate_to}. "

        # ── Build execution steps ─────────────────────────────────────────────

        steps = []
        step_idx = 1

        if need_campaign_context:
            steps.append(_step(step_idx, "campaign_tool", "Load campaign audience, keywords, brand, CTA, goals", {
                "campaign_id": campaign_id,
            }))
            step_idx += 1

        if has_knowledge_collections:
            steps.append(_step(step_idx, "knowledge_tool", "Retrieve brand and product knowledge from collections", {
                "query": prompt[:150],
                "limit": 3,
            }))
            step_idx += 1

        if need_analytics_context:
            steps.append(_step(step_idx, "analytics_tool", "Fetch recent engagement analytics for context", {
                "metric_type": "engagement_summary",
            }))
            step_idx += 1

        steps.append(_step(step_idx, "content_agent", "Generate platform-specific copy via Content Agent", {
            "platform": platform.value,
            "content_type": content_type.value,
            "include_cta": need_cta,
            "include_emoji": need_emoji,
            "include_thread": need_thread,
        }))
        step_idx += 1

        if need_image:
            steps.append(_step(step_idx, "image_agent", "Generate social image via Image Agent", {
                "platform": platform.value,
                "content_type": content_type.value,
                "aspect_ratio": PLATFORM_CONFIGS.get(platform.value, {}).get("image_ratio", "1:1"),
            }))
            step_idx += 1

        if need_hashtags:
            steps.append(_step(step_idx, "hashtag_engine", "Generate ranked hashtags with reach scores", {
                "platform": platform.value,
                "keywords": kw_list,
                "industry": "",
            }))
            step_idx += 1

        steps.append(_step(step_idx, "platform_optimizer", f"Optimize content for {platform.value} platform rules", {
            "platform": platform.value,
            "char_limit": platform_cfg.get("char_limit", 2200),
        }))
        step_idx += 1

        if need_translation:
            steps.append(_step(step_idx, "content_agent", f"Translate optimized content to {translate_to}", {
                "improvement_type": "TRANSLATE",
                "target_language": translate_to,
            }))
            step_idx += 1

        if need_scheduling:
            steps.append(_step(step_idx, "calendar_tool", "Register post in publishing calendar", {
                "schedule_type": schedule_type,
            }))
            step_idx += 1

        return {
            "thought": thought,
            "flags": {
                "need_image": need_image,
                "need_carousel": need_carousel,
                "need_cta": need_cta,
                "need_hashtags": need_hashtags,
                "need_emoji": need_emoji,
                "need_thread": need_thread,
                "need_seo_keywords": need_seo_keywords,
                "need_translation": need_translation,
                "need_scheduling": need_scheduling,
                "need_campaign_context": need_campaign_context,
                "need_analytics_context": need_analytics_context,
                "need_workflow_automation": need_workflow_automation,
            },
            "steps": steps,
            "metadata": {
                "platform": platform.value,
                "content_type": content_type.value,
                "audience": audience,
                "keywords": kw_list,
                "platform_char_limit": platform_cfg.get("char_limit", 2200),
                "platform_tone": platform_cfg.get("tone", "professional"),
            },
        }


def _step(idx: int, tool: str, description: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Build a structured plan step."""
    return {
        "step_id": f"step_{idx}",
        "tool_name": tool,
        "description": description,
        "tool_params": params,
    }
