import uuid
import pytest
from sqlalchemy.orm import Session
from api.ai.tools.crm_tool import CRMTool
from api.ai.tools.knowledge_tool import KnowledgeTool, PromptTool, CampaignTool
from api.ai.tools.web_search_tool import WebSearchTool
from api.ai.tools.registry import ToolRegistry, ToolExecutor, ToolInput


@pytest.fixture
def mock_params():
    return {
        "org_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
    }


def test_tool_registry_initialization():
    ToolRegistry.initialize()
    # Check if tools are registered
    crm = ToolRegistry.get_tool("crm_tool")
    assert crm is not None
    assert isinstance(crm, CRMTool)

    web = ToolRegistry.get_tool("web_search_tool")
    assert web is not None
    assert isinstance(web, WebSearchTool)

    schemas = ToolRegistry.to_openai_functions()
    assert len(schemas) > 0
    assert any(s["function"]["name"] == "crm_tool" for s in schemas)


def test_web_search_tool(db_session, mock_params):
    tool = WebSearchTool()
    tool_input = ToolInput(
        tool_name="web_search_tool",
        params={"query": "Generative AI", "num_results": 2},
        organization_id=mock_params["org_id"],
        user_id=mock_params["user_id"],
    )

    result = tool.execute(tool_input, db_session)
    assert result.success is True
    assert len(result.output) == 2
    assert "title" in result.output[0]


def test_tool_executor_dispatch(db_session, mock_params):
    executor = ToolExecutor(db_session)
    # Trigger web search tool dispatch
    result = executor.execute(
        tool_name="web_search_tool",
        params={"query": "Competitor campaigns"},
        organization_id=mock_params["org_id"],
        user_id=mock_params["user_id"],
    )
    assert result.success is True
    assert result.tool_name == "web_search_tool"
