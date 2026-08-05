from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.seo.manifest import SEO_AGENT_MANIFEST

class SEOAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=SEO_AGENT_MANIFEST)
