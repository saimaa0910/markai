"""
Content Agent Tools Wrapper — Sprint 7.2
=========================================
Wraps the existing ToolExecutor dispatch to allow clean, programmatic execution
of knowledge searches, templates, campaigns, and third-party integrations
without duplicating the core registry.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from api.ai.tools.registry import ToolExecutor

logger = logging.getLogger(__name__)


class ContentAgentTools:
    """Wrapper interfaces for Content Agent tool executions."""

    def __init__(self, db: Session, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.db = db
        self.org_id = str(organization_id)
        self.user_id = str(user_id)
        self.executor = ToolExecutor(db)

    def search_knowledge(
        self,
        query: str,
        collection_ids: Optional[List[uuid.UUID]] = None,
        limit: int = 5,
    ) -> List[str]:
        """Perform RAG searches using the registered knowledge_tool."""
        params: Dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if collection_ids:
            params["collection_ids"] = [str(cid) for cid in collection_ids]
            
        try:
            res = self.executor.execute(
                tool_name="knowledge_tool",
                params=params,
                organization_id=self.org_id,
                user_id=self.user_id,
            )
            if res.success and isinstance(res.output, dict):
                # Parse search results
                documents = res.output.get("documents", [])
                chunks = []
                for doc in documents:
                    title = doc.get("title", "Document")
                    text = doc.get("text", "")
                    chunks.append(f"[{title}]: {text}")
                return chunks
            return []
        except Exception as e:
            logger.warning("RAG tool execution failed (non-fatal): %s", e)
            return []

    def get_campaign_info(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Query historical details using campaign_tool."""
        try:
            res = self.executor.execute(
                tool_name="campaign_tool",
                params={"campaign_id": str(campaign_id)},
                organization_id=self.org_id,
                user_id=self.user_id,
            )
            if res.success and isinstance(res.output, dict):
                return res.output
            return {}
        except Exception as e:
            logger.warning("Campaign tool execution failed: %s", e)
            return {}

    def fetch_api_context(self, url: str) -> str:
        """Call external reference API endpoints via rest_api_tool."""
        try:
            res = self.executor.execute(
                tool_name="rest_api_tool",
                params={"url": url, "method": "GET"},
                organization_id=self.org_id,
                user_id=self.user_id,
            )
            if res.success and isinstance(res.output, dict):
                return str(res.output.get("body", ""))
            return ""
        except Exception as e:
            logger.warning("REST API context fetch failed: %s", e)
            return ""
