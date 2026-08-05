from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.image.manifest import IMAGE_AGENT_MANIFEST


class ImageAgent(BaseMarketingAgent):
    """
    Flagship Enterprise Image Generation and Modification Agent.
    Validates execution policies and coordinates image planning/execution.
    """

    def __init__(self) -> None:
        super().__init__(manifest=IMAGE_AGENT_MANIFEST)
