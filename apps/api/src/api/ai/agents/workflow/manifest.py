from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

WORKFLOW_AGENT_MANIFEST = AgentManifest(
    id="WORKFLOW",
    name="Workflow Agent",
    description="No-code automation planner, event triggers scheduler, and handler retry policy engine",
    version="1.0.0",
    category="WORKFLOW",
    tags=["marketing", "workflow"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['WORKFLOW', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['workflow_tool'],
    required_permissions=["manage_workflow"],
    default_prompt="You are an automation coordinator. You build task execution chains, schedule trigger sequences, handle conditional branching, and resolve tool execution errors.",
    default_model="gemini-1.5-flash",
    default_temperature=0.7,
    policies=AgentPolicies(
        allowed_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
        allowed_providers=["openai", "google", "groq"],
        temperature=0.7,
        max_cost=10.0,
        max_runtime_sec=300,
        max_iterations=10,
    ),
    permissions=AgentPermissions(
        allowed_tools=['workflow_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="WORKFLOW",
        description="No-code automation planner, event triggers scheduler, and handler retry policy engine",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="session",
    planner_strategy="react",
    evaluation_strategy="workflow"
)
