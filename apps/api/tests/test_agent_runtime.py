"""
Tests: Agent Runtime — Sprint 7.1
===================================
Unit + integration tests for AgentRuntime and AgentStreamingRuntime.
Uses pytest + unittest.mock (no external LLM calls).
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch, call
from api.ai.runtime.agent_runtime import AgentRuntime, AgentRunResult
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentRunStatus, AgentType, AgentStatus


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: None)
    db.rollback = MagicMock()
    return db


@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=AgentDefinition)
    agent.id = uuid.uuid4()
    agent.name = "Test Agent"
    agent.agent_type = AgentType.CUSTOM
    agent.status = AgentStatus.ACTIVE
    agent.system_prompt = "You are a helpful test agent."
    agent.prompt_template_name = None
    agent.allowed_tools = ["calculator_tool", "knowledge_tool"]
    agent.preferred_model = None
    agent.preferred_provider = None
    agent.temperature = 0.7
    agent.memory_enabled = True
    agent.max_iterations = 10
    agent.reasoning_mode = None
    agent.execution_mode = None
    agent.description = "Test agent description"
    return agent


@pytest.fixture
def mock_session(mock_agent):
    session = MagicMock(spec=AgentSession)
    session.id = uuid.uuid4()
    session.agent_id = mock_agent.id
    session.organization_id = uuid.uuid4()
    session.user_id = uuid.uuid4()
    session.agent = mock_agent
    session.is_active = True
    return session


# ─── Tests: AgentRuntime.execute() ─────────────────────────────────────────

class TestAgentRuntimeExecute:

    @patch("api.ai.runtime.agent_runtime.MemoryManager.write_memory")
    @patch("api.ai.runtime.agent_runtime.ai_evaluator")
    @patch("api.ai.runtime.agent_runtime.ai_reflector")
    @patch("api.ai.runtime.agent_runtime.AIGateway")
    @patch("api.ai.runtime.agent_runtime.build_agent_context")
    @patch("api.ai.runtime.agent_runtime.AgentPlannerService.generate_plan")
    @patch("api.ai.runtime.agent_runtime.ToolExecutor")
    def test_successful_run_no_tools(
        self, mock_tool_exec, mock_planner, mock_context, mock_gateway_cls,
        mock_reflector, mock_evaluator, mock_write_memory,
        mock_db, mock_session
    ):
        """Test a successful run with no tool calls."""
        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.chat.return_value = {
            "content": "Test response",
            "prompt_tokens": 50,
            "completion_tokens": 20,
        }
        mock_context.return_value = "system context string"
        mock_planner.return_value = {"thought": "Simple task", "steps": []}
        mock_reflector.evaluate_output.return_value = MagicMock(
            is_satisfactory=True, critique="", suggested_edits="",
            scores=MagicMock(
                hallucination_score=1.0, brand_alignment_score=1.0,
                grammar_score=1.0, tone_score=1.0, seo_score=1.0,
                completeness_score=1.0, confidence=0.9, is_satisfactory=True,
                model_dump=lambda: {},
            )
        )
        mock_evaluator.evaluate_run.return_value = MagicMock(
            overall_score=0.85, passed=True, model_dump=lambda: {}
        )

        runtime = AgentRuntime()
        result = runtime.execute(
            db=mock_db,
            session=mock_session,
            user_input="What is 2+2?",
            run_reflection=True,
            run_evaluation=True,
        )

        assert isinstance(result, AgentRunResult)
        assert result.run.status == AgentRunStatus.COMPLETED
        assert result.run.agent_output == "Test response"
        assert result.run.total_tokens == 70
        assert result.success is True
        mock_write_memory.assert_called_once()

    @patch("api.ai.runtime.agent_runtime.MemoryManager.write_memory")
    @patch("api.ai.runtime.agent_runtime.ai_evaluator")
    @patch("api.ai.runtime.agent_runtime.ai_reflector")
    @patch("api.ai.runtime.agent_runtime.AIGateway")
    @patch("api.ai.runtime.agent_runtime.build_agent_context")
    @patch("api.ai.runtime.agent_runtime.AgentPlannerService.generate_plan")
    @patch("api.ai.runtime.agent_runtime.ToolExecutor")
    def test_run_with_tool_calls(
        self, mock_tool_exec_cls, mock_planner, mock_context, mock_gateway_cls,
        mock_reflector, mock_evaluator, mock_write_memory,
        mock_db, mock_session, mock_agent
    ):
        """Test run with tool step execution."""
        mock_agent.allowed_tools = ["calculator_tool"]
        mock_session.agent = mock_agent

        mock_tool_instance = MagicMock()
        mock_tool_exec_cls.return_value = mock_tool_instance
        from api.ai.tools import ToolResult
        mock_tool_instance.execute.return_value = ToolResult(
            success=True, tool_name="calculator_tool", output={"result": 4.0}
        )

        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.chat.return_value = {"content": "4", "prompt_tokens": 30, "completion_tokens": 5}
        mock_context.return_value = "context"
        mock_planner.return_value = {
            "thought": "Use calculator",
            "steps": [{"tool_name": "calculator_tool", "tool_params": {"expression": "2+2"}, "description": "calc", "step_id": "s1"}],
        }
        mock_reflector.evaluate_output.return_value = MagicMock(
            is_satisfactory=True, critique="", suggested_edits="",
            scores=MagicMock(
                hallucination_score=1.0, brand_alignment_score=1.0, grammar_score=1.0,
                tone_score=1.0, seo_score=1.0, completeness_score=1.0, confidence=0.9,
                is_satisfactory=True, model_dump=lambda: {},
            )
        )
        mock_evaluator.evaluate_run.return_value = MagicMock(overall_score=0.9, model_dump=lambda: {})

        runtime = AgentRuntime()
        result = runtime.execute(db=mock_db, session=mock_session, user_input="2+2")

        assert result.success is True
        assert result.run.iterations == 1
        assert result.run.tool_calls is not None
        assert len(result.run.tool_calls) == 1
        assert result.run.tool_calls[0]["tool_name"] == "calculator_tool"
        assert result.run.tool_calls[0]["success"] is True

    @patch("api.ai.runtime.agent_runtime.AIGateway")
    @patch("api.ai.runtime.agent_runtime.build_agent_context")
    @patch("api.ai.runtime.agent_runtime.AgentPlannerService.generate_plan")
    @patch("api.ai.runtime.agent_runtime.ToolExecutor")
    def test_run_tool_not_in_allowed_list(
        self, mock_tool_exec_cls, mock_planner, mock_context, mock_gateway_cls,
        mock_db, mock_session, mock_agent
    ):
        """Tool calls for non-allowed tools should be denied."""
        mock_agent.allowed_tools = []
        mock_session.agent = mock_agent

        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.chat.return_value = {"content": "denied", "prompt_tokens": 10, "completion_tokens": 5}
        mock_context.return_value = "ctx"
        mock_planner.return_value = {
            "thought": "Try forbidden tool",
            "steps": [{"tool_name": "email_tool", "tool_params": {}, "description": "send email", "step_id": "s1"}],
        }

        runtime = AgentRuntime()
        with patch("api.ai.runtime.agent_runtime.ai_reflector") as mock_refl, \
             patch("api.ai.runtime.agent_runtime.ai_evaluator") as mock_eval, \
             patch("api.ai.runtime.agent_runtime.MemoryManager.write_memory"):
            mock_refl.evaluate_output.return_value = MagicMock(
                is_satisfactory=True, critique="", suggested_edits="",
                scores=MagicMock(model_dump=lambda: {}, hallucination_score=1.0,
                    brand_alignment_score=1.0, grammar_score=1.0, tone_score=1.0,
                    seo_score=1.0, completeness_score=1.0, confidence=0.9, is_satisfactory=True)
            )
            mock_eval.evaluate_run.return_value = MagicMock(model_dump=lambda: {})
            result = runtime.execute(db=mock_db, session=mock_session, user_input="send email")

        assert result.success is True
        assert result.run.tool_calls[0]["success"] is False
        assert "Permission denied" in result.run.tool_calls[0]["error"]

    @patch("api.ai.runtime.agent_runtime.AgentPlannerService.generate_plan", side_effect=RuntimeError("LLM down"))
    @patch("api.ai.runtime.agent_runtime.build_agent_context", return_value="ctx")
    @patch("api.ai.runtime.agent_runtime.ToolExecutor")
    @patch("api.ai.runtime.agent_runtime.AIGateway")
    def test_run_fails_on_planner_error(
        self, mock_gw, mock_tool, mock_ctx, mock_plan,
        mock_db, mock_session
    ):
        """Runtime must fail gracefully when planner raises."""
        mock_gw.return_value = MagicMock()
        runtime = AgentRuntime()
        result = runtime.execute(db=mock_db, session=mock_session, user_input="test")

        assert result.success is False
        assert result.run.status == AgentRunStatus.FAILED
        assert "LLM down" in result.run.error_message


# ─── Tests: Streaming Runtime ────────────────────────────────────────────────

class TestAgentStreamingRuntime:

    @patch("api.ai.runtime.streaming_runtime.MemoryManager.write_memory")
    @patch("api.ai.runtime.streaming_runtime.ai_evaluator")
    @patch("api.ai.runtime.streaming_runtime.ai_reflector")
    @patch("api.ai.runtime.streaming_runtime.AIGateway")
    @patch("api.ai.runtime.streaming_runtime.build_agent_context")
    @patch("api.ai.runtime.streaming_runtime.AgentPlannerService.generate_plan")
    @patch("api.ai.runtime.streaming_runtime.ToolExecutor")
    def test_streaming_yields_expected_events(
        self, mock_tool_exec, mock_planner, mock_context, mock_gateway_cls,
        mock_reflector, mock_evaluator, mock_write_memory,
        mock_db, mock_session
    ):
        """Stream should yield agent_start, plan, token, done events."""
        from api.ai.runtime.streaming_runtime import AgentStreamingRuntime

        mock_gateway = MagicMock()
        mock_gateway_cls.return_value = mock_gateway
        mock_gateway.stream.return_value = iter([
            {"token": "Hello", "done": False},
            {"token": " world", "done": True, "prompt_tokens": 20, "completion_tokens": 10},
        ])
        mock_context.return_value = "context"
        mock_planner.return_value = {"thought": "Direct answer", "steps": []}
        mock_reflector.evaluate_output.return_value = MagicMock(
            is_satisfactory=True, critique="", suggested_edits="",
            scores=MagicMock(model_dump=lambda: {}, hallucination_score=1.0,
                brand_alignment_score=1.0, grammar_score=1.0, tone_score=1.0,
                seo_score=1.0, completeness_score=1.0, confidence=0.9, is_satisfactory=True)
        )
        mock_evaluator.evaluate_run.return_value = MagicMock(model_dump=lambda: {"overall_score": 0.9})

        runtime = AgentStreamingRuntime()
        events = list(runtime.stream_run(
            db=mock_db,
            session=mock_session,
            user_input="Hello!",
            run_reflection=True,
            run_evaluation=True,
        ))

        event_types = []
        for e in events:
            for line in e.split("\n"):
                if line.startswith("event: "):
                    event_types.append(line[7:].strip())

        assert "agent_start" in event_types
        assert "plan" in event_types
        assert "token" in event_types
        assert "done" in event_types
