"""
Calculator Tool — Safe Mathematical Expression Evaluator
=========================================================
Evaluates mathematical expressions using Python's ast module.
Does NOT use eval() — only safe numeric AST nodes are permitted.
"""
import ast
import operator
from typing import Dict, Any
from api.ai.tools import BaseTool, ToolInput, ToolResult

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate a safe AST numeric expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_safe_eval(node.operand))
    else:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "calculator_tool"

    @property
    def description(self) -> str:
        return (
            "Evaluate a mathematical expression safely. "
            "Supports +, -, *, /, **, %, //. "
            "Example: expression='(5 + 3) * 2 / 4'"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g. '2 ** 10 / 4')",
                }
            },
            "required": ["expression"],
        }

    def execute(self, input: ToolInput, db: Any) -> ToolResult:
        expression = input.params.get("expression", "").strip()
        if not expression:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="No expression provided.",
            )
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return ToolResult(
                success=True,
                tool_name=self.name,
                output={"expression": expression, "result": result},
            )
        except ZeroDivisionError:
            return ToolResult(success=False, tool_name=self.name, error="Division by zero.")
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=f"Evaluation error: {str(e)}")
