import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api.models.agent import AgentSession
from api.ai.agents.agent import AutonomousAgent
from api.ai.agents.base.base_agent import BaseAgent
from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.exceptions import PolicyValidationError, PermissionValidationError


class BaseMarketingAgent(BaseAgent, AutonomousAgent):
    """
    Standard base class for all EAIMOS marketing agents.
    Provides policy constraints and permissions validation and then routes
    to the centralized Agent Runtime.
    """

    def __init__(self, manifest: AgentManifest) -> None:
        BaseAgent.__init__(self, manifest=manifest)
        AutonomousAgent.__init__(
            self,
            name=manifest.name,
            role=manifest.description,
            system_prompt=manifest.default_prompt,
        )

    def execute(
        self,
        db: Session,
        session: AgentSession,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Any:
        """
        Validate agent policies and permissions, then execute run via AgentRuntime.
        """
        # Validate model policy
        model = session.agent.preferred_model or self.manifest.default_model
        if self.manifest.policies.allowed_models and model not in self.manifest.policies.allowed_models:
            raise PolicyValidationError(f"Model '{model}' is not permitted by agent policies.")

        # Validate provider policy
        provider = session.agent.preferred_provider or self.manifest.policies.allowed_providers[0]
        if self.manifest.policies.allowed_providers and provider not in self.manifest.policies.allowed_providers:
            raise PolicyValidationError(f"Provider '{provider}' is not permitted by agent policies.")

        # Validate tool permissions
        allowed_tools = session.agent.allowed_tools or []
        for tool in allowed_tools:
            if tool not in self.manifest.permissions.allowed_tools:
                raise PermissionValidationError(f"Tool '{tool}' is not authorized by agent permissions.")

        # Dispatch execution to the centralized AgentRuntime
        from api.ai.runtime.agent_runtime import agent_runtime
        return agent_runtime.execute(
            db=db,
            session=session,
            user_input=user_input,
            conversation_history=conversation_history,
            run_reflection=run_reflection,
            run_evaluation=run_evaluation,
        )

    def stream(
        self,
        db: Session,
        session: AgentSession,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        run_reflection: bool = True,
        run_evaluation: bool = True,
    ) -> Any:
        """
        Validate agent policies and permissions, then execute streaming run via AgentStreamingRuntime.
        """
        # Validate model policy
        model = session.agent.preferred_model or self.manifest.default_model
        if self.manifest.policies.allowed_models and model not in self.manifest.policies.allowed_models:
            raise PolicyValidationError(f"Model '{model}' is not permitted by agent policies.")

        # Validate provider policy
        provider = session.agent.preferred_provider or self.manifest.policies.allowed_providers[0]
        if self.manifest.policies.allowed_providers and provider not in self.manifest.policies.allowed_providers:
            raise PolicyValidationError(f"Provider '{provider}' is not permitted by agent policies.")

        # Validate tool permissions
        allowed_tools = session.agent.allowed_tools or []
        for tool in allowed_tools:
            if tool not in self.manifest.permissions.allowed_tools:
                raise PermissionValidationError(f"Tool '{tool}' is not authorized by agent permissions.")

        # Dispatch execution to the streaming runtime
        from api.ai.runtime.streaming_runtime import agent_streaming_runtime
        return agent_streaming_runtime.stream_run(
            db=db,
            session=session,
            user_input=user_input,
            conversation_history=conversation_history,
            run_reflection=run_reflection,
            run_evaluation=run_evaluation,
        )
