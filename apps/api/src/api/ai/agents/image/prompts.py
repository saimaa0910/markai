from typing import Dict, Any, Optional
from api.ai.agents.image.prompt_optimizer import PromptOptimizer


class ImagePromptEngine:
    """
    Prompt engine that compiles creative visual instructions using
    organization settings, campaign context, and style libraries.
    """

    @staticmethod
    def compile_prompt(
        user_prompt: str,
        style: Optional[str] = None,
        brand_context: Optional[Dict[str, Any]] = None,
        campaign_context: Optional[Dict[str, Any]] = None,
        lighting: Optional[str] = None,
        mood: Optional[str] = None,
        template: Optional[str] = None,
        audience_context: Optional[str] = None,
        seo_keywords: Optional[str] = None,
        content_context: Optional[str] = None,
        typography: Optional[str] = None,
        color_palette: Optional[str] = None,
        composition: Optional[str] = None,
    ) -> str:
        """
        Builds a high-fidelity creative image prompt by delegating to PromptOptimizer.
        """
        return PromptOptimizer.optimize_prompt(
            user_prompt=user_prompt,
            template=template,
            style=style,
            brand_context=brand_context,
            campaign_context=campaign_context,
            audience_context=audience_context,
            seo_keywords=seo_keywords,
            content_context=content_context,
            lighting=lighting,
            camera=None,  # Available for future specific extensions
            mood=mood,
            typography=typography,
            color_palette=color_palette,
            composition=composition
        )

    @staticmethod
    def get_negative_prompt(
        user_neg: Optional[str] = None,
        org_neg: Optional[str] = None
    ) -> str:
        """
        Combines user negative prompt with org-level defaults.
        """
        default_neg = "blurry, low quality, distorted, extra limbs, ugly, text, watermark, bad anatomy, low resolution"
        neg_parts = []
        if org_neg:
            neg_parts.append(org_neg)
        if user_neg:
            neg_parts.append(user_neg)

        if not neg_parts:
            return default_neg
        return ", ".join(neg_parts)
