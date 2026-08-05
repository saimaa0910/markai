from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.analytics.manifest import ANALYTICS_AGENT_MANIFEST

class AnalyticsAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=ANALYTICS_AGENT_MANIFEST)
