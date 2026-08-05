"""
Email Tool — Send Emails via the Existing EmailService
=======================================================
Delegates entirely to api.services.email_service.EmailService.
No duplication of SMTP/email logic.
"""
from typing import Dict, Any
from api.ai.tools import BaseTool, ToolInput, ToolResult


class EmailTool(BaseTool):

    @property
    def name(self) -> str:
        return "email_tool"

    @property
    def description(self) -> str:
        return (
            "Send an email to one or more recipients. "
            "Use for outreach, notifications, campaign delivery, or follow-ups. "
            "Delegates to the platform's secure email infrastructure."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address or comma-separated list",
                },
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body (HTML or plain text)"},
                "reply_to": {"type": "string", "description": "Optional reply-to address"},
                "is_html": {"type": "boolean", "default": False, "description": "Is the body HTML?"},
            },
            "required": ["to", "subject", "body"],
        }

    def execute(self, input: ToolInput, db: Any) -> ToolResult:
        to = input.params.get("to", "").strip()
        subject = input.params.get("subject", "").strip()
        body = input.params.get("body", "").strip()
        reply_to = input.params.get("reply_to")
        is_html = bool(input.params.get("is_html", False))

        if not to or not subject or not body:
            return ToolResult(
                success=False, tool_name=self.name,
                error="'to', 'subject', and 'body' are all required.",
            )

        try:
            from api.services.email_service import send_email_background
            recipients = [addr.strip() for addr in to.split(",") if addr.strip()]

            success = True
            for recipient in recipients:
                res = send_email_background(to_email=recipient, subject=subject, html_body=body)
                if not res:
                    success = False

            return ToolResult(
                success=success,
                tool_name=self.name,
                output={
                    "recipients": recipients,
                    "subject": subject,
                    "status": "sent" if success else "failed",
                },
            )
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=f"Email send failed: {str(e)}")
