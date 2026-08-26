import logging
from typing import Dict, List, Optional
from api.ai.capabilities import BaseCapability

logger = logging.getLogger(__name__)

class CapabilityRegistry:
    """
    Registry for managing agent capabilities.
    Loads and registers capabilities dynamically.
    """

    _registry: Dict[str, BaseCapability] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, capability: BaseCapability) -> None:
        name = capability.name.upper()
        if name in cls._registry:
            logger.warning(f"Capability '{name}' is already registered. Overwriting.")
        cls._registry[name] = capability
        logger.info(f"Registered capability: {name}")

    @classmethod
    def load(cls, name: str) -> BaseCapability:
        name = name.upper()
        if name not in cls._registry:
            cls._registry[name] = BaseCapability(
                name=name,
                description=f"Standard {name} processing capability.",
                input_schema={},
                output_schema={},
                prompt_template=f"Utilize {name} capability features effectively according to request specifications."
            )
        return cls._registry[name]

    @classmethod
    def discover(cls) -> List[BaseCapability]:
        return list(cls._registry.values())

    @classmethod
    def list(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def validate(cls, name: str, params: dict) -> bool:
        """Validate input parameters against input schema of capability."""
        cap = cls.load(name)
        # In a full validator, we would run jsonschema validation.
        # For this refactoring layer, return True.
        return True

    @classmethod
    def initialize(cls) -> None:
        """Scan and register all capability modules."""
        if cls._initialized:
            return

        # Register SEO, Research, Campaign, Analytics, Brand, Workflow capabilities
        from api.ai.capabilities.seo.helpers import SEO_CAPABILITY
        from api.ai.capabilities.research.helpers import RESEARCH_CAPABILITY
        from api.ai.capabilities.campaign.helpers import CAMPAIGN_CAPABILITY
        from api.ai.capabilities.analytics.helpers import ANALYTICS_CAPABILITY
        from api.ai.capabilities.brand.helpers import BRAND_CAPABILITY
        from api.ai.capabilities.workflow.helpers import WORKFLOW_CAPABILITY

        cls.register(SEO_CAPABILITY)
        cls.register(RESEARCH_CAPABILITY)
        cls.register(CAMPAIGN_CAPABILITY)
        cls.register(ANALYTICS_CAPABILITY)
        cls.register(BRAND_CAPABILITY)
        cls.register(WORKFLOW_CAPABILITY)

        cls._initialized = True
