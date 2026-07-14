"""
Tool Calling Framework — Base Interface
========================================
Every tool in the Viptant platform must implement BaseTool.
This ensures a consistent interface for the AgentExecutor and ToolRegistry.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolInput(BaseModel):
    """
    Structured input passed to a tool execution.
    Tool-specific inputs are passed in the `params` dict.
    """
    tool_name: str
    params: Dict[str, Any]
    organization_id: str
    user_id: str


class ToolResult(BaseModel):
    """
    Standardized output from every tool execution.
    """
    success: bool
    tool_name: str
    output: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """
    Abstract base class all Viptant tools must extend.
    Provides a uniform interface for the AgentExecutor.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier used in agent configuration."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """
        JSON Schema describing the tool's input parameters.
        Used by the LLM to generate correct tool calls.
        """
        return {}

    @abstractmethod
    def execute(self, input: ToolInput, db: Any) -> ToolResult:
        """
        Execute the tool with the given input.
        Must be synchronous — async tools wrap using asyncio.
        """
        ...

    def to_openai_function(self) -> Dict[str, Any]:
        """
        Serialize this tool as an OpenAI function-calling schema.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
