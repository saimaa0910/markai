import uuid
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from api.ai.agents.image.reflection import ImageReflectionResult

logger = logging.getLogger(__name__)


class ImageEvaluationMetrics(BaseModel):
    marketing_score: float = Field(default=1.0)
    brand_score: float = Field(default=1.0)
    accessibility: float = Field(default=1.0)
    image_quality: float = Field(default=1.0)
    creativity: float = Field(default=1.0)
    composition: float = Field(default=1.0)
    seo_score: float = Field(default=1.0)
    engagement_score: float = Field(default=1.0)
    overall_score: float = Field(default=1.0)
    passed: bool = True
    critique: str = ""


class ImageEvaluator:
    """
    Automated grader for generated images and layout prompts.
    Compiles multi-dimensional marketing score cards from visual reflections.
    """

    @staticmethod
    def evaluate(
        db: Session,
        run_id: uuid.UUID,
        organization_id: uuid.UUID,
        reflection: ImageReflectionResult,
    ) -> ImageEvaluationMetrics:
        """
        Maps reflection grades to required image studio quality scores and persists them.
        """
        r = reflection.scores
        
        # Mapping rules
        marketing_score = r.marketing_impact
        brand_score = r.brand_alignment
        accessibility = r.accessibility
        image_quality = round((r.contrast + r.composition) / 2.0, 2)
        creativity = r.creativity
        composition = r.composition
        seo_score = r.readability
        engagement_score = round((r.marketing_impact + r.creativity) / 2.0, 2)
        
        # Overall weighted score
        overall = round(
            (marketing_score * 0.25) +
            (brand_score * 0.25) +
            (accessibility * 0.15) +
            (image_quality * 0.15) +
            (creativity * 0.10) +
            (seo_score * 0.10),
            2
        )

        metrics = ImageEvaluationMetrics(
            marketing_score=marketing_score,
            brand_score=brand_score,
            accessibility=accessibility,
            image_quality=image_quality,
            creativity=creativity,
            composition=composition,
            seo_score=seo_score,
            engagement_score=engagement_score,
            overall_score=overall,
            passed=reflection.is_satisfactory and overall >= 0.6,
            critique=reflection.critique,
        )

        # Persist to database agent_evaluations for integration checks
        try:
            from api.models.agent import AgentEvaluation
            eval_record = AgentEvaluation(
                run_id=run_id,
                organization_id=organization_id,
                accuracy_score=image_quality,
                brand_alignment_score=brand_score,
                completeness_score=marketing_score,
                overall_score=overall,
                is_satisfactory=reflection.is_satisfactory,
                critique=reflection.critique,
                suggested_edits=reflection.suggested_edits,
                meta_data=metrics.model_dump()
            )
            db.add(eval_record)
            db.commit()
        except Exception as e:
            logger.warning("Failed to save Image Evaluator results to agent_evaluations: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

        return metrics


# Instantiate singleton
image_evaluator = ImageEvaluator()
