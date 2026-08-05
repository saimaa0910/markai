from typing import Dict, Any, List

class BaseCapability:
    """
    Base Capability interface defining metadata used by the Manager Agent
    to coordinate execution, delegation, and parallel planning.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        estimated_runtime: int = 15,
        estimated_cost: float = 0.02,
        required_tools: List[str] = None,
        required_permissions: List[str] = None,
        supports_delegation: bool = True,
        supports_parallel_execution: bool = True,
        prompt_template: str = ""
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.estimated_runtime = estimated_runtime
        self.estimated_cost = estimated_cost
        self.required_tools = required_tools or []
        self.required_permissions = required_permissions or []
        self.supports_delegation = supports_delegation
        self.supports_parallel_execution = supports_parallel_execution
        self.prompt_template = prompt_template

    def get_system_instructions(self) -> str:
        """Return prompt instructions to append to the agent runtime."""
        return f"\n=== CAPABILITY: {self.name} ===\n{self.description}\nInstructions:\n{self.prompt_template}\n=================================\n"
