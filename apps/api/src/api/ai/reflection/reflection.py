"""
Agent Self-Reflection & Output Quality Engine
=============================================
Implements an LLM-as-a-judge reflection pass over generated agent output.

Reuses: AIGateway for the judge LLM call.
Does NOT duplicate gateway, router, or provider logic.

Scores returned (all 0.0 - 1.0):
  - hallucination_score   : factual accuracy / grounding
  - brand_alignment_score : adherence to brand voice & tone
  - grammar_score         : language quality
  - tone_score            : appropriate tone for context
  - seo_score             : SEO quality (for content agents)
  - completeness_score    : task completion
  - confidence            : judge's confidence in evaluation
  - is_satisfactory       : overall pass/fail
"""
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ReflectionScores(BaseModel):
    """Structured scores from the LLM-judge reflection pass."""
    hallucination_score: float = Field(default=1.0, ge=0.0, le=1.0)
    brand_alignment_score: float = Field(default=1.0, ge=0.0, le=1.0)
    grammar_score: float = Field(default=1.0, ge=0.0, le=1.0)
    tone_score: float = Field(default=1.0, ge=0.0, le=1.0)
    seo_score: float = Field(default=1.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    is_satisfactory: bool = True
    critique: str = ""
    suggested_edits: str = ""


class ReflectionResult(BaseModel):
    """Full reflection result including scores and text critique."""
    is_satisfactory: bool
    critique: str
    suggested_edits: str
    scores: ReflectionScores


_REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "hallucination_score": {"type": "number", "description": "0.0=high hallucination, 1.0=fully grounded"},
        "brand_alignment_score": {"type": "number", "description": "0.0=off-brand, 1.0=perfectly on-brand"},
        "grammar_score": {"type": "number", "description": "0.0=poor grammar, 1.0=perfect"},
        "tone_score": {"type": "number", "description": "0.0=wrong tone, 1.0=ideal tone"},
        "seo_score": {"type": "number", "description": "0.0=poor SEO, 1.0=excellent SEO"},
        "completeness_score": {"type": "number", "description": "0.0=incomplete, 1.0=fully complete"},
        "confidence": {"type": "number", "description": "Judge confidence in evaluation 0.0-1.0"},
        "is_satisfactory": {"type": "boolean"},
        "critique": {"type": "string", "description": "Brief critique of the output"},
        "suggested_edits": {"type": "string", "description": "Specific suggestions to improve the output"},
    },
    "required": [
        "hallucination_score", "brand_alignment_score", "grammar_score",
        "tone_score", "completeness_score", "is_satisfactory", "critique", "confidence",
    ],
}


class AIReflector:
    """
    Self-reflection & Critique Engine.
    Uses AIGateway.json_output() as an LLM judge.
    """

    def evaluate_output(
        self,
        db: Session,
        original_prompt: str,
        generated_output: str,
        organization_id: Any,
        user_id: Any,
        agent_type: str = "CUSTOM",
        brand_voice: str = "",
        model_name: Optional[str] = None,
    ) -> ReflectionResult:
        """
        Evaluate generated output quality against task intent.
        Calls AIGateway.json_output() as an LLM judge.
        Returns ReflectionResult with structured scores and critique.
        """
        system_instruction = (
            "You are an expert AI Output Quality Judge for an enterprise marketing platform. "
            "Evaluate the GENERATED OUTPUT against the ORIGINAL PROMPT and BRAND VOICE. "
            "Return a JSON object with numerical scores (0.0-1.0) and qualitative critique.\n\n"
            f"Agent Type: {agent_type}\n"
            f"Brand Voice Guidelines: {brand_voice or 'Professional, clear, engaging.'}\n\n"
            "Scoring Criteria:\n"
            "- hallucination_score: Does the output contain fabricated facts? 1.0=none, 0.0=many\n"
            "- brand_alignment_score: Does it match the brand voice? 1.0=perfect, 0.0=misaligned\n"
            "- grammar_score: Grammar and writing quality\n"
            "- tone_score: Is the tone appropriate for context?\n"
            "- seo_score: Is it SEO-friendly? (keyword density, headings, structure)\n"
            "- completeness_score: Does it fully address the user's request?\n"
            "- confidence: Your confidence in this evaluation\n"
            "- is_satisfactory: Overall pass (true) or fail (false)\n"
            "- critique: Brief 1-2 sentence critique\n"
            "- suggested_edits: Specific improvement suggestions"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": (
                    f"ORIGINAL PROMPT:\n{original_prompt[:1000]}\n\n"
                    f"GENERATED OUTPUT:\n{generated_output[:2000]}"
                ),
            },
        ]

        try:
            from api.ai.gateway.coordinator import AIGateway
            gateway = AIGateway()
            result = gateway.json_output(
                db=db,
                messages=messages,
                schema=_REFLECTION_SCHEMA,
                organization_id=organization_id,
                user_id=user_id,
                model_name=model_name,
            )

            scores = ReflectionScores(
                hallucination_score=float(result.get("hallucination_score", 1.0)),
                brand_alignment_score=float(result.get("brand_alignment_score", 1.0)),
                grammar_score=float(result.get("grammar_score", 1.0)),
                tone_score=float(result.get("tone_score", 1.0)),
                seo_score=float(result.get("seo_score", 1.0)),
                completeness_score=float(result.get("completeness_score", 1.0)),
                confidence=float(result.get("confidence", 0.9)),
                is_satisfactory=bool(result.get("is_satisfactory", True)),
                critique=str(result.get("critique", "")),
                suggested_edits=str(result.get("suggested_edits", "")),
            )

            return ReflectionResult(
                is_satisfactory=scores.is_satisfactory,
                critique=scores.critique,
                suggested_edits=scores.suggested_edits,
                scores=scores,
            )

        except Exception as e:
            logger.warning("Reflection engine error (returning safe defaults): %s", e)
            # On gateway failure, return safe pass-through result
            scores = ReflectionScores()
            return ReflectionResult(
                is_satisfactory=True,
                critique=f"Reflection unavailable: {str(e)[:100]}",
                suggested_edits="",
                scores=scores,
            )


# Module-level singleton
ai_reflector = AIReflector()
