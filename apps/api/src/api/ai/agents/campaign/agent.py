from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.campaign.manifest import CAMPAIGN_AGENT_MANIFEST

class CampaignAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=CAMPAIGN_AGENT_MANIFEST)
