"""
Tests: Reflection Engine — Sprint 7.1
======================================
Tests for AIReflector covering score parsing, fail-safe behavior.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch
from api.ai.reflection.reflection import AIReflector, ReflectionScores


class TestAIReflector:

    def make_db_and_ids(self):
        db = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        return db, org_id, user_id

    @patch("api.ai.gateway.coordinator.AIGateway")
    def test_satisfactory_output(self, mock_gateway_cls):
        """High scores should produce is_satisfactory=True."""
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.json_output.return_value = {
            "hallucination_score": 0.95,
            "brand_alignment_score": 0.90,
            "grammar_score": 0.97,
            "tone_score": 0.92,
            "seo_score": 0.88,
            "completeness_score": 0.93,
            "confidence": 0.91,
            "is_satisfactory": True,
            "critique": "Excellent output.",
            "suggested_edits": "",
        }

        reflector = AIReflector()
        db, org_id, user_id = self.make_db_and_ids()
        result = reflector.evaluate_output(
            db=db, original_prompt="Write a product description",
            generated_output="Premium product for modern users.",
            organization_id=org_id, user_id=user_id,
        )

        assert result.is_satisfactory is True
        assert result.scores.hallucination_score == 0.95
        assert result.scores.confidence == 0.91

    @patch("api.ai.gateway.coordinator.AIGateway")
    def test_unsatisfactory_output(self, mock_gateway_cls):
        """Low scores and is_satisfactory=False should be propagated."""
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.json_output.return_value = {
            "hallucination_score": 0.30,
            "brand_alignment_score": 0.40,
            "grammar_score": 0.55,
            "tone_score": 0.50,
            "seo_score": 0.20,
            "completeness_score": 0.45,
            "confidence": 0.80,
            "is_satisfactory": False,
            "critique": "Output contains potential hallucinations.",
            "suggested_edits": "Add citations and verify facts.",
        }

        reflector = AIReflector()
        db, org_id, user_id = self.make_db_and_ids()
        result = reflector.evaluate_output(
            db=db, original_prompt="Describe our product",
            generated_output="Our product has 1000 years of history and cures cancer.",
            organization_id=org_id, user_id=user_id,
        )

        assert result.is_satisfactory is False
        assert result.scores.hallucination_score == 0.30
        assert "hallucination" in result.critique.lower()

    @patch("api.ai.gateway.coordinator.AIGateway")
    def test_gateway_failure_returns_safe_defaults(self, mock_gateway_cls):
        """On gateway error, reflection must return safe defaults (not raise)."""
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.json_output.side_effect = RuntimeError("LLM timeout")

        reflector = AIReflector()
        db, org_id, user_id = self.make_db_and_ids()
        result = reflector.evaluate_output(
            db=db, original_prompt="Test", generated_output="Test response",
            organization_id=org_id, user_id=user_id,
        )

        assert result is not None
        assert result.is_satisfactory is True  # Safe default
        assert "Reflection unavailable" in result.critique

    def test_reflection_scores_clamped(self):
        """Scores must stay within 0.0-1.0 range."""
        # Pydantic v2 rejects out of bounds scores with ValidationError
        from pydantic_core import ValidationError
        with pytest.raises(ValidationError):
            ReflectionScores(
                hallucination_score=1.5,
            )


class TestEvaluator:

    @patch("api.ai.reflection.reflection.ai_reflector")
    def test_overall_score_computed(self, mock_reflector):
        """Overall score should be a weighted average of all dimensions."""
        from api.ai.evaluation.evaluator import AIEvaluator

        mock_reflector.evaluate_output.return_value = MagicMock(
            is_satisfactory=True, critique="Good", suggested_edits="",
            scores=MagicMock(
                hallucination_score=1.0, brand_alignment_score=1.0,
                grammar_score=1.0, tone_score=1.0, seo_score=1.0,
                completeness_score=1.0, confidence=0.9, is_satisfactory=True,
            )
        )

        evaluator = AIEvaluator()
        db = MagicMock()
        org_id = uuid.uuid4()

        with patch.object(evaluator, "_persist"):
            metrics = evaluator.evaluate_run(
                db=db,
                run_id=uuid.uuid4(),
                organization_id=org_id,
                user_id=uuid.uuid4(),
                agent_output="Hello world",
                user_input="Say hello",
                plan={"thought": "Direct", "steps": []},
                tool_calls=[],
                total_tokens=100,
                latency_ms=500,
                cost_usd=0.001,
            )

        assert 0.0 <= metrics.overall_score <= 1.0
        assert metrics.cost_score > 0.9  # Low cost → high score
        assert metrics.latency_score > 0.9  # Fast → high score
