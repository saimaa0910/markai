from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session
from api.models.agent import AgentSession

class IAgent(ABC):
    @property
    @abstractmethod
    def manifest(self):
        pass

    @abstractmethod
    def execute(self, db: Session, session: AgentSession, user_input: str, **kwargs) -> Dict[str, Any]:
        pass
