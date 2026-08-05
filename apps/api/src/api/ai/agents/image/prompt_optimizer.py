from typing import Dict, Any, Optional
from api.ai.agents.image.constants import STYLE_LIBRARY
from api.ai.agents.image.helpers import LIGHTING_PRESETS, CAMERA_PRESETS, MOOD_PRESETS
from api.ai.agents.image.templates import TEMPLATES


class PromptOptimizer:
    """
    Prompt compilation optimizer.
    Sequentially combines user requests, templates, styles, design assets, and marketing guidelines.
    """

    @staticmethod
    def optimize_prompt(
        user_prompt: str,
        template: Optional[str] = None,
        style: Optional[str] = None,
        brand_context: Optional[Dict[str, Any]] = None,
        campaign_context: Optional[Dict[str, Any]] = None,
        audience_context: Optional[str] = None,
        seo_keywords: Optional[str] = None,
        content_context: Optional[str] = None,
        lighting: Optional[str] = None,
        camera: Optional[str] = None,
        mood: Optional[str] = None,
        typography: Optional[str] = None,
        color_palette: Optional[str] = None,
        composition: Optional[str] = None,
    ) -> str:
        parts = []

        # 1. Base Prompt description
        parts.append(user_prompt.strip())

        # 2. Add visual templates
        if template:
            template_desc = TEMPLATES.get(template.lower())
            if template_desc:
                parts.append(f"Visual format: {template_desc}")

        # 3. Add styling styles preset
        if style:
            style_desc = STYLE_LIBRARY.get(style.lower())
            if style_desc:
                parts.append(f"Style: {style_desc}")

        if camera:
            camera_desc = CAMERA_PRESETS.get(camera.lower(), camera)
            parts.append(f"Camera angle: {camera_desc}")

        if lighting:
            lighting_desc = LIGHTING_PRESETS.get(lighting.lower(), lighting)
            parts.append(f"Lighting: {lighting_desc}")

        if mood:
            mood_desc = MOOD_PRESETS.get(mood.lower(), mood)
            parts.append(f"Mood: {mood_desc}")

        # 4. Design details
        if composition:
            parts.append(f"Composition layout: {composition}")
        if typography:
            parts.append(f"Typography elements: {typography}")
        if color_palette:
            parts.append(f"Design color palette: {color_palette}")

        # 5. Inject Brand Context
        if brand_context:
            brand_voice = brand_context.get("brand_voice")
            brand_colors = brand_context.get("color_palette")
            logo_desc = brand_context.get("logo_description")

            brand_parts = []
            if brand_colors:
                brand_parts.append(f"colors: {brand_colors}")
            if logo_desc:
                brand_parts.append(f"logo detailing: {logo_desc}")
            if brand_voice:
                brand_parts.append(f"guidelines: {brand_voice}")

            if brand_parts:
                parts.append("Brand voice guidelines: " + " | ".join(brand_parts))

        # 6. Inject Campaign Context
        if campaign_context:
            keywords = campaign_context.get("keywords")
            if keywords:
                parts.append(f"Campaign background context: {keywords}")

        # 7. Inject Audience Profile
        if audience_context:
            parts.append(f"Designed for target audience segment: {audience_context}")

        # 8. Inject SEO keywords
        if seo_keywords:
            parts.append(f"SEO overlay keywords context: {seo_keywords}")

        # 9. Inject Content Context
        if content_context:
            parts.append(f"Associated content brief: {content_context}")

        return ". ".join(parts)
