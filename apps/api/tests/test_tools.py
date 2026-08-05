"""
Tests: New Sprint 7.1 Tools
============================
Unit tests for: CalculatorTool, RESTAPITool, AnalyticsTool, EmailTool
"""
import pytest
from unittest.mock import MagicMock, patch
from api.ai.tools import ToolInput


# ─── CalculatorTool ───────────────────────────────────────────────────────────

class TestCalculatorTool:
    def make_input(self, expression: str) -> ToolInput:
        return ToolInput(
            tool_name="calculator_tool",
            params={"expression": expression},
            organization_id=str(__import__("uuid").uuid4()),
            user_id=str(__import__("uuid").uuid4()),
        )

    def test_addition(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("2 + 3"), None)
        assert result.success is True
        assert result.output["result"] == 5.0

    def test_multiplication(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("4 * 7"), None)
        assert result.success is True
        assert result.output["result"] == 28.0

    def test_power(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("2 ** 10"), None)
        assert result.success is True
        assert result.output["result"] == 1024.0

    def test_complex_expression(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("(5 + 3) * 2 / 4"), None)
        assert result.success is True
        assert result.output["result"] == 4.0

    def test_division_by_zero(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("1 / 0"), None)
        assert result.success is False
        assert "zero" in result.error.lower()

    def test_empty_expression(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input(""), None)
        assert result.success is False

    def test_disallowed_function(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("__import__('os').system('echo hi')"), None)
        assert result.success is False

    def test_negation(self):
        from api.ai.tools.calculator_tool import CalculatorTool
        tool = CalculatorTool()
        result = tool.execute(self.make_input("-5 + 10"), None)
        assert result.success is True
        assert result.output["result"] == 5.0


# ─── RESTAPITool ─────────────────────────────────────────────────────────────

class TestRESTAPITool:
    def make_input(self, url: str, method: str = "GET", body=None) -> ToolInput:
        return ToolInput(
            tool_name="rest_api_tool",
            params={"url": url, "method": method, "body": body},
            organization_id=str(__import__("uuid").uuid4()),
            user_id=str(__import__("uuid").uuid4()),
        )

    def test_blocks_localhost(self):
        from api.ai.tools.rest_api_tool import RESTAPITool
        tool = RESTAPITool()
        result = tool.execute(self.make_input("http://localhost:8000/api"), None)
        assert result.success is False
        assert "blocked" in result.error.lower()

    def test_blocks_private_ip(self):
        from api.ai.tools.rest_api_tool import RESTAPITool
        tool = RESTAPITool()
        result = tool.execute(self.make_input("http://192.168.1.1/admin"), None)
        assert result.success is False

    def test_empty_url(self):
        from api.ai.tools.rest_api_tool import RESTAPITool
        tool = RESTAPITool()
        result = tool.execute(self.make_input(""), None)
        assert result.success is False
        assert "URL" in result.error

    @patch("httpx.Client")
    def test_successful_get(self, mock_client_cls):
        from api.ai.tools.rest_api_tool import RESTAPITool
        tool = RESTAPITool()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "ok"}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = tool.execute(self.make_input("https://api.example.com/data"), None)
        assert result.success is True
        assert result.output["status_code"] == 200


# ─── AnalyticsTool ───────────────────────────────────────────────────────────

class TestAnalyticsTool:
    def make_input(self, metric_type: str) -> ToolInput:
        return ToolInput(
            tool_name="analytics_tool",
            params={"metric_type": metric_type, "limit": 5},
            organization_id=str(__import__("uuid").uuid4()),
            user_id=str(__import__("uuid").uuid4()),
        )

    def test_invalid_metric_type(self):
        from api.ai.tools.analytics_tool import AnalyticsTool
        tool = AnalyticsTool()
        result = tool.execute(self.make_input("invalid_metric"), None)
        assert result.success is False
        assert "Unknown metric_type" in result.error

    def test_agent_runs_query(self):
        from api.ai.tools.analytics_tool import AnalyticsTool
        tool = AnalyticsTool()
        mock_db = MagicMock()
        mock_db.scalars.return_value.all.return_value = []
        result = tool._get_agent_runs(mock_db, __import__("uuid").uuid4(), None, 5)
        assert result.success is True
        assert result.output["total_runs"] == 0
        assert result.output["success_rate"] == 100.0


# ─── EmailTool ───────────────────────────────────────────────────────────────

class TestEmailTool:
    def make_input(self, to: str = "", subject: str = "", body: str = "") -> ToolInput:
        return ToolInput(
            tool_name="email_tool",
            params={"to": to, "subject": subject, "body": body},
            organization_id=str(__import__("uuid").uuid4()),
            user_id=str(__import__("uuid").uuid4()),
        )

    def test_missing_fields(self):
        from api.ai.tools.email_tool import EmailTool
        tool = EmailTool()
        result = tool.execute(self.make_input(to="test@test.com"), None)
        assert result.success is False
        assert "required" in result.error

    def test_empty_to(self):
        from api.ai.tools.email_tool import EmailTool
        tool = EmailTool()
        result = tool.execute(self.make_input(subject="Hi", body="Hello"), None)
        assert result.success is False

    @patch("api.services.email_service.send_email_background")
    def test_successful_send(self, mock_send_email):
        from api.ai.tools.email_tool import EmailTool
        tool = EmailTool()

        mock_send_email.return_value = True

        inp = ToolInput(
            tool_name="email_tool",
            params={"to": "user@example.com", "subject": "Test Subject", "body": "Hello there!"},
            organization_id=str(__import__("uuid").uuid4()),
            user_id=str(__import__("uuid").uuid4()),
        )
        result = tool.execute(inp, None)
        assert result.success is True
        assert result.output["recipients"] == ["user@example.com"]
        mock_send_email.assert_called_once_with(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="Hello there!"
        )
