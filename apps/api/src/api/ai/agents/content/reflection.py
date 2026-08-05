"""
Content Agent Reflection Engine — Sprint 7.2
=============================================
Leverages the core AIReflector judge to evaluate grammar, brand, SEO, and completeness.
Implements auto-correction (auto-rewrite) when quality scores fall below threshold.
"""
import uuid
import logging
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from api.ai.reflection.reflection import ai_reflector, ReflectionResult
from api.ai.gateway.coordinator import AIGateway

logger = logging.getLogger(__name__)


class ContentReflector:
    """Orchestrates quality evaluation and auto-correction loops for generated content."""

    def __init__(self, threshold: float = 0.70) -> None:
        self.threshold = threshold
        self.gateway = AIGateway()

    def review_and_correct(
        self,
        db: Session,
        prompt: str,
        content: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        brand_voice: str = "",
        model_name: Optional[str] = None,
        max_attempts: int = 2,
    ) -> Tuple[str, ReflectionResult, int]:
        """
        Reviews content. If is_satisfactory is False or score is below threshold,
        it automatically issues a rewrite instructions loop to the LLM.
        Returns Tuple of (final_content, reflection_result, attempts_used).
        """
        current_content = content
        attempts = 0
        last_result = None

        while attempts < max_attempts:
            attempts += 1
            logger.info("Running reflection pass, attempt %d", attempts)
            
            try:
                # Delegate to the platform's core judge
                result: ReflectionResult = ai_reflector.evaluate_output(
                    db=db,
                    original_prompt=prompt,
                    generated_output=current_content,
                    organization_id=organization_id,
                    user_id=user_id,
                    brand_voice=brand_voice,
                    model_name=model_name,
                )
                last_result = result
            except Exception as e:
                logger.warning("Reflection judge execution failed: %s. Proceeding with defaults.", e)
                # Fail-safe: return default satisfactory result
                return current_content, ReflectionResult(is_satisfactory=True, critique="Judge failed, auto-approved."), attempts

            # Evaluate thresholds
            overall = result.scores.confidence if hasattr(result.scores, "confidence") else 0.9
            passed = result.is_satisfactory and overall >= self.threshold

            if passed:
                logger.info("Content passed reflection checks. Score: %0.2f", overall)
                return current_content, result, attempts

            # If not passed, rewrite content using AIGateway with critique
            logger.warning("Content failed reflection checks. Score: %0.2f. Critique: %s. Retrying...", overall, result.critique)
            
            rewrite_prompt = (
                f"You are a Content Editor. Rewrite the following content to fix the highlighted issues.\n\n"
                f"Original Prompt: {prompt}\n\n"
                f"Current Draft:\n{current_content}\n\n"
                f"Critique / Issues to Fix:\n{result.critique}\n"
                f"Suggested Edits:\n{result.suggested_edits}\n\n"
                f"Write the revised content in full. Do not include any meta-text, conversational prefixes, or commentary."
            )

            try:
                gw_result = self.gateway.chat(
                    db=db,
                    messages=[{"role": "user", "content": rewrite_prompt}],
                    organization_id=organization_id,
                    user_id=user_id,
                    model_name=model_name,
                )
                current_content = gw_result.get("content", current_content)
            except Exception as e:
                logger.error("Auto-correction rewrite LLM call failed: %s", e)
                break

        # Return final state even if threshold wasn't met after max attempts
        return current_content, last_result or ReflectionResult(is_satisfactory=True, critique="Auto-passed on timeout."), attempts
