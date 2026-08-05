"""
Agent Evaluation & Scoring Engine
===================================
Computes multi-dimensional quality scores for an AgentRun and persists
them to the agent_evaluations table.

Reuses:
  - AgentRun model (existing)
  - AgentEvaluation model (new, added Sprint 7.1)
  - ReflectionResult from AIReflector (ai/reflection/reflection.py)
  - No duplication of gateway, cost tracking, or telemetry.

Score Dimensions (all 0.0 - 1.0):
  accuracy_score         - from reflection hallucination
  cost_score             - normalized cost vs. budget
  latency_score          - normalized latency vs. target
  reasoning_score        - quality of the plan thought
  tool_usage_score       - tool call success rate
  knowledge_usage_score  - knowledge retrieval relevance
  brand_alignment_score  - from reflection brand score
  safety_score           - absence of blocked content
  overall_score          - weighted average
"""
import logging
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Scoring weights for overall_score computation
SCORE_WEIGHTS = {
    "accuracy_score": 0.25,
    "brand_alignment_score": 0.20,
    "safety_score": 0.15,
    "completeness_score": 0.15,
    "reasoning_score": 0.10,
    "tool_usage_score": 0.05,
    "knowledge_usage_score": 0.05,
    "cost_score": 0.03,
    "latency_score": 0.02,
}

# Latency targets for normalization
TARGET_LATENCY_MS = 5000   # 5 s target
MAX_LATENCY_MS = 30000     # 30 s = 0.0 score

# Cost targets for normalization (USD)
TARGET_COST_USD = 0.01
MAX_COST_USD = 0.10


class EvaluationMetrics(BaseModel):
    """Complete evaluation metrics for one AgentRun."""
    faithfulness_score: float = Field(default=1.0)
    relevance_score: float = Field(default=1.0)
    coherence_score: float = Field(default=1.0)
    accuracy_score: float = Field(default=1.0)
    cost_score: float = Field(default=1.0)
    latency_score: float = Field(default=1.0)
    reasoning_score: float = Field(default=1.0)
    tool_usage_score: float = Field(default=1.0)
    knowledge_usage_score: float = Field(default=1.0)
    brand_alignment_score: float = Field(default=1.0)
    safety_score: float = Field(default=1.0)
    hallucination_score: float = Field(default=1.0)
    grammar_score: float = Field(default=1.0)
    tone_score: float = Field(default=1.0)
    completeness_score: float = Field(default=1.0)
    overall_score: float = Field(default=1.0)
    confidence: float = Field(default=0.9)
    passed: bool = True


class AIEvaluator:
    """
    Evaluates LLM generation quality using automated criteria.
    Combines reflection scores + run telemetry into a unified evaluation.
    """

    def evaluate_run(
        self,
        db: Session,
        run_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        agent_output: str,
        user_input: str,
        plan: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[list] = None,
        total_tokens: int = 0,
        latency_ms: int = 0,
        cost_usd: float = 0.0,
        agent_type: str = "CUSTOM",
        brand_voice: str = "",
        model_name: Optional[str] = None,
    ) -> EvaluationMetrics:
        """
        Compute full evaluation metrics for a completed AgentRun.
        Persists results to agent_evaluations table.
        """
        # 1. Run reflection pass
        from api.ai.reflection.reflection import ai_reflector
        reflection = ai_reflector.evaluate_output(
            db=db,
            original_prompt=user_input,
            generated_output=agent_output,
            organization_id=organization_id,
            user_id=user_id,
            agent_type=agent_type,
            brand_voice=brand_voice,
            model_name=model_name,
        )

        # 2. Compute telemetry-based scores
        cost_score = self._score_cost(cost_usd)
        latency_score = self._score_latency(latency_ms)
        tool_usage_score = self._score_tool_usage(tool_calls)
        reasoning_score = self._score_reasoning(plan)

        # 3. Map reflection scores
        r = reflection.scores
        accuracy_score = r.hallucination_score
        brand_alignment_score = r.brand_alignment_score
        completeness_score = r.completeness_score
        grammar_score = r.grammar_score
        tone_score = r.tone_score
        hallucination_score = r.hallucination_score
        knowledge_usage_score = 1.0  # Set by knowledge tool outcome if available
        safety_score = 1.0  # Assumed clean — Gateway security pipeline already validated

        # Check tool results for knowledge tool success
        if tool_calls:
            knowledge_calls = [tc for tc in tool_calls if "knowledge" in str(tc.get("tool_name", ""))]
            if knowledge_calls:
                successful_kc = sum(1 for tc in knowledge_calls if tc.get("success"))
                knowledge_usage_score = successful_kc / len(knowledge_calls) if knowledge_calls else 1.0

        # 4. Compute overall weighted score
        dim_scores = {
            "accuracy_score": accuracy_score,
            "brand_alignment_score": brand_alignment_score,
            "safety_score": safety_score,
            "completeness_score": completeness_score,
            "reasoning_score": reasoning_score,
            "tool_usage_score": tool_usage_score,
            "knowledge_usage_score": knowledge_usage_score,
            "cost_score": cost_score,
            "latency_score": latency_score,
        }
        overall = sum(dim_scores[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        passed = overall >= 0.6 and reflection.is_satisfactory

        metrics = EvaluationMetrics(
            faithfulness_score=accuracy_score,
            relevance_score=completeness_score,
            coherence_score=grammar_score,
            accuracy_score=accuracy_score,
            cost_score=cost_score,
            latency_score=latency_score,
            reasoning_score=reasoning_score,
            tool_usage_score=tool_usage_score,
            knowledge_usage_score=knowledge_usage_score,
            brand_alignment_score=brand_alignment_score,
            safety_score=safety_score,
            hallucination_score=hallucination_score,
            grammar_score=grammar_score,
            tone_score=tone_score,
            completeness_score=completeness_score,
            overall_score=round(overall, 4),
            confidence=r.confidence,
            passed=passed,
        )

        # 5. Persist evaluation to DB
        self._persist(
            db=db,
            run_id=run_id,
            organization_id=organization_id,
            metrics=metrics,
            critique=reflection.critique,
            suggested_edits=reflection.suggested_edits,
            is_satisfactory=reflection.is_satisfactory,
        )

        return metrics

    def _score_cost(self, cost_usd: float) -> float:
        """Normalize cost: 0 USD = 1.0, MAX_COST_USD+ = 0.0"""
        if cost_usd <= 0:
            return 1.0
        if cost_usd >= MAX_COST_USD:
            return 0.0
        return 1.0 - (cost_usd / MAX_COST_USD)

    def _score_latency(self, latency_ms: int) -> float:
        """Normalize latency: 0ms = 1.0, MAX_LATENCY_MS+ = 0.0"""
        if latency_ms <= 0:
            return 1.0
        if latency_ms >= MAX_LATENCY_MS:
            return 0.0
        return 1.0 - (latency_ms / MAX_LATENCY_MS)

    def _score_tool_usage(self, tool_calls: Optional[list]) -> float:
        """Score tool usage by success rate."""
        if not tool_calls:
            return 1.0  # No tools required = full score
        successful = sum(1 for tc in tool_calls if tc.get("success"))
        return successful / len(tool_calls)

    def _score_reasoning(self, plan: Optional[Dict[str, Any]]) -> float:
        """Score reasoning quality by plan thought length and step count."""
        if not plan:
            return 0.5
        thought = plan.get("thought", "")
        steps = plan.get("steps", [])
        thought_score = min(1.0, len(thought) / 200)  # longer thought = better
        steps_score = min(1.0, len(steps) / 5)        # up to 5 steps ideal
        return round((thought_score + steps_score) / 2, 4)

    def _persist(
        self,
        db: Session,
        run_id: uuid.UUID,
        organization_id: uuid.UUID,
        metrics: EvaluationMetrics,
        critique: str,
        suggested_edits: str,
        is_satisfactory: bool,
    ) -> None:
        """Persist evaluation to agent_evaluations table."""
        try:
            from api.models.agent import AgentEvaluation
            evaluation = AgentEvaluation(
                run_id=run_id,
                organization_id=organization_id,
                accuracy_score=metrics.accuracy_score,
                cost_score=metrics.cost_score,
                latency_score=metrics.latency_score,
                reasoning_score=metrics.reasoning_score,
                tool_usage_score=metrics.tool_usage_score,
                knowledge_usage_score=metrics.knowledge_usage_score,
                brand_alignment_score=metrics.brand_alignment_score,
                safety_score=metrics.safety_score,
                hallucination_score=metrics.hallucination_score,
                grammar_score=metrics.grammar_score,
                tone_score=metrics.tone_score,
                completeness_score=metrics.completeness_score,
                overall_score=metrics.overall_score,
                confidence=metrics.confidence,
                critique=critique,
                suggested_edits=suggested_edits,
                is_satisfactory=is_satisfactory,
                meta_data={
                    "faithfulness_score": metrics.faithfulness_score,
                    "relevance_score": metrics.relevance_score,
                    "coherence_score": metrics.coherence_score,
                    "passed": metrics.passed,
                },
            )
            db.add(evaluation)
            db.commit()
        except Exception as e:
            logger.warning("Failed to persist AgentEvaluation: %s", e)
            try:
                db.rollback()
            except Exception:
                pass


# Module-level singleton
ai_evaluator = AIEvaluator()
