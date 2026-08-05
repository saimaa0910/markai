from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.brand.manifest import BRAND_AGENT_MANIFEST

class BrandAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=BRAND_AGENT_MANIFEST)
