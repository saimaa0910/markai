from api.ai.agents.base.base_marketing_agent import BaseMarketingAgent
from api.ai.agents.workflow.manifest import WORKFLOW_AGENT_MANIFEST

class WorkflowAgent(BaseMarketingAgent):
    def __init__(self) -> None:
        super().__init__(manifest=WORKFLOW_AGENT_MANIFEST)
