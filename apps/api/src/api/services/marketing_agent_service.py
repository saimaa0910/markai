import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.ai.agents.base.registry import AgentRegistry, map_category_to_agent_type
from api.models.agent import AgentSession, AgentDefinition, AgentStatus

logger = logging.getLogger(__name__)

class MarketingAgentService:
    """
    Unified service for managing and executing all capability-driven marketing agents.
    Eliminates duplicated agent services (SEOService, ResearchService, etc.)
    by routing calls dynamically based on Agent Manifests.
    """

    @staticmethod
    def execute_agent(
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        agent_id: str,
        user_input: str,
        session_id: Optional[uuid.UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        AgentRegistry.initialize()
        agent = AgentRegistry.get(agent_id)
        
        # Resolve or create session
        if not session_id:
            db_type = map_category_to_agent_type(agent.manifest.category)
            agent_def = db.query(AgentDefinition).filter(
                AgentDefinition.organization_id == organization_id,
                AgentDefinition.agent_type == db_type,
                AgentDefinition.deleted_at.is_(None)
            ).first()
            
            if not agent_def:
                AgentRegistry.sync_to_db(db)
                agent_def = db.query(AgentDefinition).filter(
                    AgentDefinition.organization_id == organization_id,
                    AgentDefinition.agent_type == db_type,
                    AgentDefinition.deleted_at.is_(None)
                ).first()
                
            agent_session = AgentSession(
                organization_id=organization_id,
                user_id=user_id,
                agent_id=agent_def.id,
                title=f"{agent.manifest.name} Session",
            )
            db.add(agent_session)
            db.commit()
            db.refresh(agent_session)
        else:
            agent_session = db.query(AgentSession).filter(
                AgentSession.id == session_id
            ).first()
            if not agent_session:
                raise ValueError(f"Session '{session_id}' not found.")

        # Execute agent execution loop
        result = agent.execute(
            db=db,
            session=agent_session,
            user_input=user_input,
            conversation_history=conversation_history,
        )
        
        return {
            "session_id": str(agent_session.id),
            "result": result
        }

    @staticmethod
    def stream_agent(
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        agent_id: str,
        user_input: str,
        session_id: Optional[uuid.UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Any:
        AgentRegistry.initialize()
        agent = AgentRegistry.get(agent_id)
        
        # Resolve or create session
        if not session_id:
            db_type = map_category_to_agent_type(agent.manifest.category)
            agent_def = db.query(AgentDefinition).filter(
                AgentDefinition.organization_id == organization_id,
                AgentDefinition.agent_type == db_type,
                AgentDefinition.deleted_at.is_(None)
            ).first()
            
            if not agent_def:
                AgentRegistry.sync_to_db(db)
                agent_def = db.query(AgentDefinition).filter(
                    AgentDefinition.organization_id == organization_id,
                    AgentDefinition.agent_type == db_type,
                    AgentDefinition.deleted_at.is_(None)
                ).first()
                
            agent_session = AgentSession(
                organization_id=organization_id,
                user_id=user_id,
                agent_id=agent_def.id,
                title=f"{agent.manifest.name} Session",
            )
            db.add(agent_session)
            db.commit()
            db.refresh(agent_session)
        else:
            agent_session = db.query(AgentSession).filter(
                AgentSession.id == session_id
            ).first()
            if not agent_session:
                raise ValueError(f"Session '{session_id}' not found.")

        # Execute streaming run
        return agent.stream(
            db=db,
            session=agent_session,
            user_input=user_input,
            conversation_history=conversation_history,
        )
