"""
Knowledge Tool — RAG-powered search through the organization's knowledge base.
"""
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from api.ai.tools import BaseTool, ToolInput, ToolResult


class KnowledgeTool(BaseTool):
    @property
    def name(self) -> str:
        return "knowledge_tool"

    @property
    def description(self) -> str:
        return (
            "Search the organization's knowledge base using semantic similarity. "
            "Use this tool to find relevant documents, brand guidelines, product info, "
            "or any information stored in the knowledge platform."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant knowledge",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return (default: 3)",
                    "default": 3,
                },
            },
            "required": ["query"],
        }

    def execute(self, input: ToolInput, db: Session) -> ToolResult:
        try:
            org_id = uuid.UUID(input.organization_id)
            user_id = uuid.UUID(input.user_id)
            query = input.params.get("query", "")
            limit = input.params.get("limit", 3)

            from api.services.knowledge import KnowledgeService
            chunks = KnowledgeService.query_similar_chunks(
                db=db,
                query_text=query,
                organization_id=org_id,
                user_id=user_id,
                limit=limit,
            )

            results = [
                {
                    "chunk_id": str(c.id),
                    "document_id": str(c.document_id),
                    "content": c.content,
                }
                for c in chunks
            ]

            return ToolResult(
                success=True,
                tool_name=self.name,
                output=results,
                metadata={"result_count": len(results)},
            )

        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=str(e))


class PromptTool(BaseTool):
    """
    Retrieves rendered prompt templates from the Prompt Platform.
    """
    @property
    def name(self) -> str:
        return "prompt_tool"

    @property
    def description(self) -> str:
        return (
            "Retrieve and render prompt templates from the Prompt Library. "
            "Use this tool to get a specific prompt template by name."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt_name": {
                    "type": "string",
                    "description": "Name of the prompt template to retrieve",
                },
                "variables": {
                    "type": "object",
                    "description": "Variable substitutions for the prompt template",
                },
            },
            "required": ["prompt_name"],
        }

    def execute(self, input: ToolInput, db: Session) -> ToolResult:
        try:
            org_id = uuid.UUID(input.organization_id)
            prompt_name = input.params.get("prompt_name", "")
            variables = input.params.get("variables", {})

            from api.services.prompt import PromptService
            prompt = PromptService.get_latest_prompt(
                db=db, name=prompt_name, organization_id=org_id
            )

            if not prompt:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error=f"Prompt template '{prompt_name}' not found",
                )

            # Simple variable substitution: {{variable_name}} → value
            content = prompt.content
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

            return ToolResult(
                success=True,
                tool_name=self.name,
                output={"prompt_name": prompt_name, "content": content, "version": prompt.version},
            )

        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=str(e))


class CampaignTool(BaseTool):
    """
    Provides campaign status, analytics, and management capabilities.
    """
    @property
    def name(self) -> str:
        return "campaign_tool"

    @property
    def description(self) -> str:
        return (
            "Access campaign data including active campaigns, performance metrics, "
            "and campaign status. Use to query campaign information or analytics."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_campaigns", "get_analytics"],
                    "description": "The campaign action to perform",
                },
                "limit": {
                    "type": "integer",
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

            from api.models.campaign import Campaign, CampaignAnalytics

            if action == "list_campaigns":
                campaigns = (
                    db.query(Campaign)
                    .filter(
                        Campaign.organization_id == org_id,
                        Campaign.deleted_at.is_(None),
                    )
                    .limit(limit)
                    .all()
                )
                data = [
                    {
                        "id": str(c.id),
                        "title": c.title,
                        "status": c.status.value,
                        "channel": c.channel.value,
                        "budget": float(c.budget),
                    }
                    for c in campaigns
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
