from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.research.manifest import RESEARCH_AGENT_MANIFEST

class ResearchAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=RESEARCH_AGENT_MANIFEST)
