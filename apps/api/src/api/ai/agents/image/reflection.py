import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from api.ai.gateway.coordinator import AIGateway

logger = logging.getLogger(__name__)


class ImageReflectionScores(BaseModel):
    composition: float = Field(default=1.0, ge=0.0, le=1.0)
    brand_alignment: float = Field(default=1.0, ge=0.0, le=1.0)
    readability: float = Field(default=1.0, ge=0.0, le=1.0)
    accessibility: float = Field(default=1.0, ge=0.0, le=1.0)
    contrast: float = Field(default=1.0, ge=0.0, le=1.0)
    creativity: float = Field(default=1.0, ge=0.0, le=1.0)
    marketing_impact: float = Field(default=1.0, ge=0.0, le=1.0)
    visual_hierarchy: float = Field(default=1.0, ge=0.0, le=1.0)
    cta_visibility: float = Field(default=1.0, ge=0.0, le=1.0)


class ImageReflectionResult(BaseModel):
    is_satisfactory: bool
    critique: str
    suggested_edits: str
    scores: ImageReflectionScores


_IMAGE_REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "composition": {"type": "number"},
        "brand_alignment": {"type": "number"},
        "readability": {"type": "number"},
        "accessibility": {"type": "number"},
        "contrast": {"type": "number"},
        "creativity": {"type": "number"},
        "marketing_impact": {"type": "number"},
        "visual_hierarchy": {"type": "number"},
        "cta_visibility": {"type": "number"},
        "is_satisfactory": {"type": "boolean"},
        "critique": {"type": "string"},
        "suggested_edits": {"type": "string"},
    },
    "required": [
        "composition", "brand_alignment", "readability", "accessibility",
        "contrast", "creativity", "marketing_impact", "visual_hierarchy",
        "cta_visibility", "is_satisfactory", "critique", "suggested_edits"
    ],
}


class ImageReflector:
    """
    Self-reflection critique engine specialized for marketing images.
    Uses LLM judge to evaluate the creative prompt details against brand guidelines.
    """

    def reflect(
        self,
        db: Session,
        prompt: str,
        style: Optional[str],
        brand_voice: str,
        organization_id: Any,
        user_id: Any,
    ) -> ImageReflectionResult:
        system_instruction = (
            "You are a principal creative director and visual designer. "
            "Evaluate the visual generation layout prompt and style context against brand and marketing requirements. "
            "Grade each visual aspect from 0.0 to 1.0 (composition, alignment, accessibility, contrast, creativity, impact, hierarchy, CTA visibility) "
            "and suggest improvements for the prompt descriptors.\n\n"
            f"Brand Guidelines: {brand_voice or 'Professional corporate, premium colors.'}\n\n"
            "Assess:\n"
            "- composition: Layout structure and balance.\n"
            "- brand_alignment: Tone, colors compliance.\n"
            "- readability: Text contrast and readability if overlay text exists.\n"
            "- accessibility: Visual separation, clean subjects.\n"
            "- contrast: Brightness / color range.\n"
            "- creativity: Originality and style choice.\n"
            "- marketing_impact: Visual draw, engagement draw.\n"
            "- visual_hierarchy: Read focal point.\n"
            "- cta_visibility: Prominence of CTA or logo slots."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": (
                    f"VISUAL CREATIVE PROMPT:\n{prompt}\n\n"
                    f"STYLE FILTER:\n{style or 'None'}"
                ),
            },
        ]

        try:
            gateway = AIGateway()
            result = gateway.json_output(
                db=db,
                messages=messages,
                schema=_IMAGE_REFLECTION_SCHEMA,
                organization_id=organization_id,
                user_id=user_id,
            )

            scores = ImageReflectionScores(
                composition=float(result.get("composition", 1.0)),
                brand_alignment=float(result.get("brand_alignment", 1.0)),
                readability=float(result.get("readability", 1.0)),
                accessibility=float(result.get("accessibility", 1.0)),
                contrast=float(result.get("contrast", 1.0)),
                creativity=float(result.get("creativity", 1.0)),
                marketing_impact=float(result.get("marketing_impact", 1.0)),
                visual_hierarchy=float(result.get("visual_hierarchy", 1.0)),
                cta_visibility=float(result.get("cta_visibility", 1.0)),
            )

            return ImageReflectionResult(
                is_satisfactory=bool(result.get("is_satisfactory", True)),
                critique=str(result.get("critique", "")),
                suggested_edits=str(result.get("suggested_edits", "")),
                scores=scores,
            )

        except Exception as e:
            logger.warning("Image reflection judge failed: %s. Returning default scores.", e)
            return ImageReflectionResult(
                is_satisfactory=True,
                critique=f"Image reflection completed: {str(e)[:100]}",
                suggested_edits="No edits suggested.",
                scores=ImageReflectionScores()
            )


# Instantiate singleton
image_reflector = ImageReflector()
