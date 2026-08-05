from api.ai.capabilities import BaseCapability

SHARED_CAPABILITY = BaseCapability(
    name="SHARED",
    description="Enterprise SHARED optimization and processing capabilities.",
    input_schema={"type": "object", "properties": {"prompt": {"type": "string"}}},
    output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
    estimated_runtime=10,
    estimated_cost=0.01,
    required_tools=[],
    required_permissions=[],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard enterprise SHARED capability guidelines."
)
