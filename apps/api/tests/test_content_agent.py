"""
Tests: Content Agent Core — Sprint 7.2
========================================
Verifies ContentAgent execute generation and improvement loops with mocks.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch
from api.ai.agents.content.agent import ContentAgent
from api.ai.agents.content.constants import ContentType, ImprovementType


class TestContentAgent:

    @patch("api.ai.agents.content.executor.ContentExecutor.generate")
    def test_execute_generation(self, mock_generate):
        mock_generate.return_value = {
            "title": "Test content",
            "generated_content": "Premium generated copy.",
            "overall_score": 0.95,
            "reflection_passed": True
        }

        agent = ContentAgent()
        db = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = agent.execute_generation(
            db=db,
            organization_id=org_id,
            user_id=user_id,
            content_type=ContentType.BLOG_ARTICLE,
            prompt="Write a post about SaaS builders",
            run_reflection=False,
            run_evaluation=False
        )

        assert result["overall_score"] == 0.95
        assert "Premium" in result["generated_content"]
        mock_generate.assert_called_once()

    @patch("api.ai.agents.content.executor.ContentExecutor.improve")
    def test_execute_improvement(self, mock_improve):
        mock_improve.return_value = "Improved copy version."

        agent = ContentAgent()
        db = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = agent.execute_improvement(
            db=db,
            organization_id=org_id,
            user_id=user_id,
            content="Raw draft text",
            improvement_type=ImprovementType.REWRITE
        )

        assert result == "Improved copy version."
        mock_improve.assert_called_once()
