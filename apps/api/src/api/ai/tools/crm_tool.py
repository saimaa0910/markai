"""
CRM Tool — Read/Write access to Companies, Contacts, Leads
"""
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from api.ai.tools import BaseTool, ToolInput, ToolResult
from api.models.contact import Contact
from api.models.company import Company
from api.models.lead import Lead


class CRMTool(BaseTool):
    @property
    def name(self) -> str:
        return "crm_tool"

    @property
    def description(self) -> str:
        return (
            "Read and search CRM data including contacts, companies, and leads. "
            "Use this tool to look up customer information, find contacts by name or email, "
            "list recent leads, or get company details."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_contacts", "list_companies", "list_leads", "search_contacts"],
                    "description": "The CRM action to perform",
                },
                "query": {
                    "type": "string",
                    "description": "Search query for search actions",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 10)",
                    "default": 10,
                },
            },
            "required": ["action"],
        }

    def execute(self, input: ToolInput, db: Session) -> ToolResult:
        try:
            org_id = uuid.UUID(input.organization_id)
            action = input.params.get("action")
            limit = input.params.get("limit", 10)

            if action == "list_contacts":
                records = (
                    db.query(Contact)
                    .filter(
                        Contact.organization_id == org_id,
                        Contact.deleted_at.is_(None),
                    )
                    .limit(limit)
                    .all()
                )
                data = [
                    {
                        "id": str(r.id),
                        "full_name": r.full_name,
                        "email": r.email,
                        "phone": r.phone,
                    }
                    for r in records
                ]
                return ToolResult(success=True, tool_name=self.name, output=data)

            elif action == "list_companies":
                records = (
                    db.query(Company)
                    .filter(
                        Company.organization_id == org_id,
                        Company.deleted_at.is_(None),
                    )
                    .limit(limit)
                    .all()
                )
                data = [
                    {"id": str(r.id), "name": r.name, "industry": r.industry}
                    for r in records
                ]
                return ToolResult(success=True, tool_name=self.name, output=data)

            elif action == "list_leads":
                records = (
                    db.query(Lead)
                    .filter(
                        Lead.organization_id == org_id,
                        Lead.deleted_at.is_(None),
                    )
                    .limit(limit)
                    .all()
                )
                data = [
                    {
                        "id": str(r.id),
                        "title": r.title,
                        "status": r.status.value if r.status else None,
                        "value": float(r.value) if r.value else 0,
                    }
                    for r in records
                ]
                return ToolResult(success=True, tool_name=self.name, output=data)

            elif action == "search_contacts":
                query_str = input.params.get("query", "")
                records = (
                    db.query(Contact)
                    .filter(
                        Contact.organization_id == org_id,
                        Contact.deleted_at.is_(None),
                        Contact.full_name.ilike(f"%{query_str}%"),
                    )
                    .limit(limit)
                    .all()
                )
                data = [
                    {"id": str(r.id), "full_name": r.full_name, "email": r.email}
                    for r in records
                ]
                return ToolResult(success=True, tool_name=self.name, output=data)

            else:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error=f"Unknown action: {action}",
                )

        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=str(e))
