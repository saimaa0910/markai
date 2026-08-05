from api.ai.agents.base.interfaces import IAgent
from api.ai.agents.base.manifest import AgentManifest

class BaseAgent(IAgent):
    """
    Standard base class representing an AI agent.
    """
    def __init__(self, manifest: AgentManifest) -> None:
        self._manifest = manifest

    @property
    def manifest(self) -> AgentManifest:
        return self._manifest
