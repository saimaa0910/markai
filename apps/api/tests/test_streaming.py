"""
Tests: Content Streaming Service — Sprint 7.2
==============================================
Verifies the SSE stream generator yields expected status, plan, tokens, and metrics.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch
from api.ai.agents.content.service import ContentAgentService, _sse
from api.ai.agents.content.constants import ContentType
from api.models.agent import AgentSession, AgentDefinition


class TestContentStreaming:

    @patch("api.ai.agents.content.service.MemoryManager.write_memory")
    @patch("api.ai.gateway.coordinator.AIGateway")
    def test_stream_generate_content(self, mock_gateway_cls, mock_write_memory):
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        # Stream yields 2 token items and then ends
        mock_gateway.stream.return_value = [
            {"token": "Drafting", "done": False},
            {"token": " content...", "done": True, "prompt_tokens": 10, "completion_tokens": 5}
        ]

        db = MagicMock()
        agent = MagicMock(spec=AgentDefinition)
        agent.id = uuid.uuid4()
        agent.memory_enabled = False

        session = MagicMock(spec=AgentSession)
        session.id = uuid.uuid4()
        session.organization_id = uuid.uuid4()
        session.user_id = uuid.uuid4()
        session.agent_id = agent.id
        session.agent = agent

        # Call stream
        events = list(ContentAgentService.stream_generate_content(
            db=db,
            session=session,
            content_type=ContentType.BLOG_ARTICLE,
            prompt="Simple topic prompt",
            run_reflection=False,
            run_evaluation=False,
        ))

        # Parse out event types
        event_types = []
        for event in events:
            for line in event.split("\n"):
                if line.startswith("event: "):
                    event_types.append(line[7:].strip())

        assert "status" in event_types
        assert "plan" in event_types
        assert "llm_token" in event_types
        assert "completed" in event_types

    def test_sse_formatter(self):
        result = _sse("status", {"message": "Active"})
        assert "event: status\n" in result
        assert 'data: {"message": "Active"}\n\n' in result
