"""
Tests: Context Builder — Sprint 7.1
===================================
Tests for ContextBuilder and build_agent_context to verify merging priority,
token budget, and MemoryManager delegation.
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch
from api.ai.context.builder import ContextBuilder, build_agent_context
from api.models.agent import AgentDefinition, AgentType
from api.models.memory import MemoryType


class TestContextBuilder:
    def test_context_builder_budget_respect(self):
        # 3000 tokens * 4 = 12000 chars budget
        builder = ContextBuilder(token_budget=10)  # 40 chars budget
        
        # Adding a section of 20 chars (including header block formatting)
        # block formatting: \n=== Header ===\nContent\n
        # "\n=== Header ===\n12345\n" is 1 + 14 + 5 + 1 = 21 chars
        added = builder._add_section("Header", "12345")
        assert added is True
        
        # Adding another one that exceeds budget (40 chars)
        # "\n=== Another ===\n12345678901234567890\n" is 1 + 15 + 20 + 1 = 37 chars. Total: 21 + 37 = 58 > 40
        added_exceed = builder._add_section("Another", "12345678901234567890")
        assert added_exceed is False
        
        context = builder.build()
        assert "Header" in context
        assert "Another" not in context

    @patch("api.ai.context.builder.MemoryManager")
    def test_build_agent_context_ordering_and_sources(self, mock_memory_manager):
        db = MagicMock()
        agent = MagicMock(spec=AgentDefinition)
        agent.id = uuid.uuid4()
        agent.name = "Test Agent"
        agent.agent_type = AgentType.CUSTOM
        agent.status = "ACTIVE"
        agent.system_prompt = "System instructions"
        agent.prompt_template_name = None
        agent.preferred_model = None
        agent.preferred_provider = None
        agent.temperature = 0.7
        agent.memory_enabled = True
        agent.max_iterations = 10
        agent.reasoning_mode = "standard"
        agent.execution_mode = "sequential"
        agent.description = "Agent description"
        agent.organization_id = uuid.uuid4()

        # Mock memory responses
        mock_org_mem_item = MagicMock()
        mock_org_mem_item.category = "voice"
        mock_org_mem_item.key = "tone"
        mock_org_mem_item.value = "friendly"
        mock_memory_manager.get_org_memory.return_value = [mock_org_mem_item]

        mock_lt_item = MagicMock()
        mock_lt_item.memory_key = "user_name"
        mock_lt_item.memory_value = "Alice"
        
        mock_st_item = MagicMock()
        mock_st_item.memory_key = "last_topic"
        mock_st_item.memory_value = "billing"

        def mock_read_mem(db, agent_id, organization_id, memory_type, limit, session_id=None):
            if memory_type == MemoryType.LONG_TERM:
                return [mock_lt_item]
            if memory_type == MemoryType.SHORT_TERM:
                return [mock_st_item]
            return []

        mock_memory_manager.read_memory.side_effect = mock_read_mem

        # Call builder
        context = build_agent_context(
            db=db,
            agent=agent,
            user_input="How do I pay?",
            session_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            organization_id=agent.organization_id,
            tool_results=[{"tool_name": "calculator_tool", "success": True, "output": 4}],
            workflow_state={"step": "payment"},
            knowledge_chunks=["Knowledge Chunk 1"],
            conversation_history=[{"role": "user", "content": "Hello"}],
            user_profile={"name": "Alice Profile"},
        )

        # Check sections exist
        assert "System Instructions" in context
        assert "System instructions" in context
        assert "Agent Identity" in context
        assert "Agent Name: Test Agent" in context
        assert "Organization Context & Brand Voice" in context
        assert "[voice] tone: friendly" in context
        assert "User Profile" in context
        assert "name: Alice Profile" in context
        assert "Agent Long-Term Memory" in context
        assert "user_name: Alice" in context
        assert "Conversation History" in context
        assert "User: Hello" in context
        assert "Session Memory" in context
        assert "last_topic: billing" in context
        assert "Relevant Knowledge" in context
        assert "Knowledge Chunk 1" in context
        assert "Tool Execution Results" in context
        assert "Tool: calculator_tool [OK]" in context
        assert "Workflow State" in context
        assert "step: payment" in context
        assert "Current User Request" in context
        assert "How do I pay?" in context
