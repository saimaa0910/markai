"""
Tool Execution Runtime Engine
==============================
Wires the ai/executor stub to the production ToolExecutor.
No duplication — delegates entirely to ai/tools/registry.py.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from api.ai.tools import ToolResult


class ToolExecutorBridge:
    """
    Executes registered tools dynamically based on agent plans.
    Bridges the ai/executor interface to the production ToolExecutor.
    """

    def __init__(self, db: Session) -> None:
        from api.ai.tools.registry import ToolExecutor
        self._executor = ToolExecutor(db)

    def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        organization_id: str,
        user_id: str,
    ) -> ToolResult:
        """
        Invoke tool by name with parameters.
        Delegates to ToolExecutor from ai/tools/registry.py.
        """
        return self._executor.execute(
            tool_name=tool_name,
            params=tool_args,
            organization_id=organization_id,
            user_id=user_id,
        )

    def execute_tool_dict(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        organization_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Convenience wrapper returning a plain dict."""
        result = self.execute_tool(tool_name, tool_args, organization_id, user_id)
        return {
            "tool_name": result.tool_name,
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata,
        }


tool_executor = ToolExecutorBridge
