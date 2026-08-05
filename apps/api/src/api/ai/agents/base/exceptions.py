class AgentError(Exception):
    """Base class for all agent-related exceptions."""
    pass

class AgentRegistrationError(AgentError):
    pass

class AgentNotFoundError(AgentError):
    pass

class PolicyValidationError(AgentError):
    pass

class PermissionValidationError(AgentError):
    pass
