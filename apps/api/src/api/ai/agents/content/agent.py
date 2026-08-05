"""
Content Agent — Sprint 7.2
===========================
Wraps the execution entry points of the Enterprise Content Agent.
Extends AutonomousAgent pattern.
"""
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.content.manifest import CONTENT_AGENT_MANIFEST
from api.ai.agents.content.constants import ContentType, ImprovementType
from api.ai.agents.content.executor import ContentExecutor


class ContentAgent(BaseMarketingAgent):
    """
    Production-ready Enterprise Content Generation Agent.
    Plugs into the EAIMOS runtime framework.
    """

    def __init__(self) -> None:
        super().__init__(manifest=CONTENT_AGENT_MANIFEST)

    def execute_generation(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        content_type: ContentType,
        prompt: str,
        brand_voice_override: Optional[str] = None,
        forbidden_words: Optional[List[str]] = None,
        preferred_words: Optional[List[str]] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        target_audience: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Dict[str, Any]:
        """Perform a complete generation execute flow."""
        executor = ContentExecutor(db, organization_id, user_id)
        return executor.generate(
            content_type=content_type,
            prompt=prompt,
            brand_voice_override=brand_voice_override,
            forbidden_words=forbidden_words,
            preferred_words=preferred_words,
            knowledge_collections=knowledge_collections,
            target_audience=target_audience,
            keywords=keywords,
            preferred_model=preferred_model,
            temperature=temperature,
            run_reflection=run_reflection,
            run_evaluation=run_evaluation,
        )

    def execute_improvement(
        self,
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        improvement_type: ImprovementType,
        target_tone: Optional[str] = None,
        target_audience: Optional[str] = None,
        target_language: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> str:
        """Perform content improvement edit/rewrite pass."""
        executor = ContentExecutor(db, organization_id, user_id)
        return executor.improve(
            content=content,
            improvement_type=improvement_type,
            target_tone=target_tone,
            target_audience=target_audience,
            target_language=target_language,
            keywords=keywords,
            preferred_model=preferred_model,
            temperature=temperature,
        )


# Global singleton instance
content_agent = ContentAgent()
