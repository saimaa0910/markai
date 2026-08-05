"""
REST API Tool — HTTP Caller for External APIs
=============================================
Allows agents to call external REST endpoints (GET / POST).
Enforces a 10-second timeout and blocks calls to internal hosts.
"""
import re
from typing import Dict, Any
from api.ai.tools import BaseTool, ToolInput, ToolResult

_BLOCKED_HOSTS = re.compile(
    r"(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)", re.IGNORECASE
)


class RESTAPITool(BaseTool):

    @property
    def name(self) -> str:
        return "rest_api_tool"

    @property
    def description(self) -> str:
        return (
            "Call an external REST API endpoint. "
            "Supports GET and POST methods with optional JSON body and headers. "
            "Returns the HTTP status code and response body."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to call (must be HTTPS for external APIs)"},
                "method": {"type": "string", "enum": ["GET", "POST"], "default": "GET"},
                "headers": {"type": "object", "description": "Optional HTTP headers as key-value pairs"},
                "body": {"type": "object", "description": "Optional JSON body for POST requests"},
                "timeout": {"type": "integer", "description": "Request timeout in seconds (max 10)", "default": 10},
            },
            "required": ["url"],
        }

    def execute(self, input: ToolInput, db: Any) -> ToolResult:
        url = input.params.get("url", "").strip()
        method = input.params.get("method", "GET").upper()
        headers = input.params.get("headers") or {}
        body = input.params.get("body")
        timeout = min(int(input.params.get("timeout", 10)), 10)

        if not url:
            return ToolResult(success=False, tool_name=self.name, error="URL is required.")

        if _BLOCKED_HOSTS.search(url):
            return ToolResult(success=False, tool_name=self.name, error="Calls to internal/private hosts are blocked.")

        try:
            import httpx
            with httpx.Client(timeout=timeout) as client:
                if method == "POST":
                    response = client.post(url, json=body, headers=headers)
                else:
                    response = client.get(url, headers=headers)

            try:
                resp_body = response.json()
            except Exception:
                resp_body = response.text[:2000]

            return ToolResult(
                success=response.status_code < 400,
                tool_name=self.name,
                output={
                    "status_code": response.status_code,
                    "body": resp_body,
                    "url": url,
                    "method": method,
                },
                error=None if response.status_code < 400 else f"HTTP {response.status_code}",
            )
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=f"Request failed: {str(e)}")
