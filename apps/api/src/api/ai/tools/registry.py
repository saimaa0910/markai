"""
Tool Registry — Central registry of all available tools.
ToolExecutor — Executes a named tool from the registry.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from api.ai.tools import BaseTool, ToolInput, ToolResult
from api.ai.tools.crm_tool import CRMTool
from api.ai.tools.knowledge_tool import KnowledgeTool, PromptTool, CampaignTool
from api.ai.tools.web_search_tool import WebSearchTool
from api.ai.tools.workflow_tool import WorkflowTool
# Sprint 7.1 — New tools
from api.ai.tools.calculator_tool import CalculatorTool
from api.ai.tools.rest_api_tool import RESTAPITool
from api.ai.tools.email_tool import EmailTool
from api.ai.tools.analytics_tool import AnalyticsTool
from api.ai.agents.image.tools import ImageGenerateTool, ImageEditTool, ImageUpscaleTool


class ToolRegistry:
    """
    Central registry of all available tools.
    Instantiated once; tools are singletons.
    """

    _registry: Dict[str, BaseTool] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Register all built-in tools."""
        if cls._initialized:
            return
        tools: List[BaseTool] = [
            CRMTool(),
            KnowledgeTool(),
            PromptTool(),
            CampaignTool(),
            WebSearchTool(),
            WorkflowTool(),
            # Sprint 7.1 — New tools
            CalculatorTool(),
            RESTAPITool(),
            EmailTool(),
            AnalyticsTool(),
            # Sprint 7.4 — Image tools
            ImageGenerateTool(),
            ImageEditTool(),
            ImageUpscaleTool(),
        ]
        for tool in tools:
            cls._registry[tool.name] = tool
            if tool.name == "image_generate_tool":
                cls._registry["image_generation_tool"] = tool
        cls._initialized = True

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        cls.initialize()
        if name == "image_generation_tool":
            return cls._registry.get("image_generate_tool")
        return cls._registry.get(name)

    @classmethod
    def list_tools(cls) -> List[BaseTool]:
        cls.initialize()
        return list(cls._registry.values())

    @classmethod
    def get_allowed_tools(cls, allowed_tool_names: List[str]) -> List[BaseTool]:
        cls.initialize()
        return [cls._registry[n] for n in allowed_tool_names if n in cls._registry]

    @classmethod
    def to_openai_functions(cls, allowed_tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return OpenAI function-calling schemas for the given tools (or all tools)."""
        cls.initialize()
        if allowed_tool_names is not None:
            tools = cls.get_allowed_tools(allowed_tool_names)
        else:
            tools = cls.list_tools()
        return [t.to_openai_function() for t in tools]

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register a custom/extension tool at runtime."""
        cls.initialize()
        cls._registry[tool.name] = tool


class ToolExecutor:
    """
    Executes a named tool by dispatching to the ToolRegistry.
    All exceptions are caught and returned as ToolResult(success=False).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, tool_name: str, params: Dict[str, Any], organization_id: str, user_id: str) -> ToolResult:
        """Execute a registered tool by name with given params."""
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' is not registered in the ToolRegistry",
            )

        tool_input = ToolInput(
            tool_name=tool_name,
            params=params,
            organization_id=organization_id,
            user_id=user_id,
        )

        try:
            return tool.execute(tool_input, self.db)
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool execution raised an unhandled exception: {str(e)}",
            )
