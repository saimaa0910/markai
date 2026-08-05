import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from api.models.agent import AgentDefinition, AgentStatus, AgentType
from api.models.organization import Organization
from api.ai.agents.base.base_agent import BaseAgent
from api.ai.agents.base.exceptions import AgentRegistrationError, AgentNotFoundError

logger = logging.getLogger(__name__)


def map_category_to_agent_type(category: str) -> AgentType:
    """Map string categories to existing AgentType database enums."""
    mapping = {
        "MARKETING": AgentType.MARKETING,
        "CONTENT": AgentType.CONTENT,
        "CAMPAIGN": AgentType.CAMPAIGN,
        "CRM": AgentType.CRM,
        "ANALYTICS": AgentType.ANALYTICS,
        "RESEARCH": AgentType.RESEARCH,
        "SEO": AgentType.SEO,
        "WORKFLOW": AgentType.WORKFLOW,
        "SALES": AgentType.SALES,
        "SUPPORT": AgentType.SUPPORT,
        "SOCIAL": AgentType.SOCIAL,
    }
    return mapping.get(category.upper(), AgentType.CUSTOM)


class AgentRegistry:
    """
    Central registry of all available AI Agents in the system.
    Handles discovery, manifest validation, and database seeding.
    """

    _registry: Dict[str, BaseAgent] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        agent_id = agent.manifest.id.upper()
        if agent_id in cls._registry:
            logger.warning(f"Agent '{agent_id}' is already registered. Overwriting.")
        cls._registry[agent_id] = agent
        logger.info(f"Registered agent: {agent_id}")

    @classmethod
    def unregister(cls, agent_id: str) -> None:
        agent_id = agent_id.upper()
        if agent_id in cls._registry:
            del cls._registry[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")

    @classmethod
    def get(cls, agent_id: str) -> BaseAgent:
        agent_id = agent_id.upper()
        if agent_id not in cls._registry:
            raise AgentNotFoundError(f"Agent '{agent_id}' is not registered.")
        return cls._registry[agent_id]

    @classmethod
    def list(cls) -> List[BaseAgent]:
        return list(cls._registry.values())

    @classmethod
    def discover(cls) -> List[BaseAgent]:
        return cls.list()

    @classmethod
    def load(cls, agent_id: str) -> BaseAgent:
        return cls.get(agent_id)

    @classmethod
    def health(cls) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "registered_agents_count": len(cls._registry),
            "agents": [a.manifest.id for a in cls.list()]
        }

    @classmethod
    def sync_to_db(cls, db: Session) -> None:
        """
        Scan all organizations in the DB and synchronize AgentDefinitions
        with the registry's manifests.
        """
        orgs = db.query(Organization).all()
        if not orgs:
            logger.warning("No organizations found to synchronize agents for.")
            return

        for org in orgs:
            for agent in cls.list():
                db_type = map_category_to_agent_type(agent.manifest.category)

                # Check if this agent definition exists in the organization
                db_agent = db.query(AgentDefinition).filter(
                    AgentDefinition.organization_id == org.id,
                    AgentDefinition.agent_type == db_type,
                    AgentDefinition.deleted_at.is_(None)
                ).first()

                # Compile system prompt from manifest default prompt + capabilities system instructions
                compiled_prompt = agent.manifest.default_prompt or ""
                from api.ai.capabilities.registry import CapabilityRegistry
                CapabilityRegistry.initialize()
                for cap_name in agent.manifest.capabilities:
                    try:
                        cap = CapabilityRegistry.load(cap_name)
                        compiled_prompt += cap.get_system_instructions()
                    except Exception as cap_err:
                        logger.warning(f"Error loading capability '{cap_name}' instructions: {cap_err}")

                if not db_agent:
                    # Insert missing agent definition
                    db_agent = AgentDefinition(
                        name=agent.manifest.name,
                        description=agent.manifest.description,
                        agent_type=db_type,
                        status=AgentStatus.ACTIVE,
                        allowed_tools=agent.manifest.permissions.allowed_tools,
                        preferred_model=agent.manifest.default_model,
                        temperature=agent.manifest.default_temperature,
                        max_tokens=agent.manifest.default_max_tokens,
                        system_prompt=compiled_prompt,
                        memory_enabled=agent.manifest.streaming_support,
                        organization_id=org.id,
                    )
                    db.add(db_agent)
                    logger.info(f"Seeded agent definition '{agent.manifest.id}' for organization '{org.slug}'")
                else:
                    # Update metadata-driven properties
                    db_agent.name = agent.manifest.name
                    db_agent.description = agent.manifest.description
                    db_agent.allowed_tools = agent.manifest.permissions.allowed_tools
                    db_agent.system_prompt = compiled_prompt
                    db.add(db_agent)
                    logger.info(f"Synchronized agent definition '{agent.manifest.id}' for organization '{org.slug}'")
        db.commit()

    @classmethod
    def initialize(cls) -> None:
        """Load and register all built-in marketing agents."""
        if cls._initialized:
            return

        # Initialize capability registry first
        from api.ai.capabilities.registry import CapabilityRegistry
        CapabilityRegistry.initialize()

        # Register Content Agent
        from api.ai.agents.content.agent import ContentAgent
        cls.register(ContentAgent())

        # Register Actual Agent implementations
        from api.ai.agents.seo.agent import SEOAgent
        from api.ai.agents.research.agent import ResearchAgent
        from api.ai.agents.campaign.agent import CampaignAgent
        from api.ai.agents.analytics.agent import AnalyticsAgent
        from api.ai.agents.brand.agent import BrandAgent
        from api.ai.agents.workflow.agent import WorkflowAgent
        from api.ai.agents.image.agent import ImageAgent
        from api.ai.agents.social.agent import SocialAgent

        cls.register(SEOAgent())
        cls.register(ResearchAgent())
        cls.register(CampaignAgent())
        cls.register(AnalyticsAgent())
        cls.register(BrandAgent())
        cls.register(WorkflowAgent())
        cls.register(ImageAgent())
        cls.register(SocialAgent())

        # Register other placeholders
        from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
        from api.ai.agents.base.placeholder_manifests import PLACEHOLDERS
        actual_ids = {"CONTENT", "SEO", "RESEARCH", "CAMPAIGN", "ANALYTICS", "BRAND", "WORKFLOW", "IMAGE", "SOCIAL"}
        for manifest in PLACEHOLDERS:
            if manifest.id.upper() not in actual_ids:
                cls.register(BaseMarketingAgent(manifest=manifest))

        cls._initialized = True
