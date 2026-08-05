from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

CONTENT_AGENT_MANIFEST = AgentManifest(
    id="CONTENT",
    name="Enterprise Content Agent",
    description="Flagship Content Writer and copy editor.",
    version="1.0.0",
    category="CONTENT",
    tags=["marketing", "copywriting", "blog", "email"],
    icon="📝",
    color="#7c3aed",
    owner="Viptant",
    visibility="public",
    capabilities=["CONTENT", "RAG", "TOOLS"],
    supported_providers=["openai", "google"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=["knowledge_tool", "calculator_tool", "analytics_tool"],
    required_permissions=["create_content"],
    default_prompt="You write and edit top-grade brand-aligned copy.",
    default_model="gemini-1.5-flash",
    default_temperature=0.7,
    policies=AgentPolicies(
        allowed_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
        allowed_providers=["openai", "google"],
        temperature=0.7,
        max_cost=10.0,
        max_runtime_sec=300,
        max_iterations=10,
    ),
    permissions=AgentPermissions(
        allowed_tools=["knowledge_tool", "calculator_tool", "analytics_tool"]
    ),
    metadata=AgentMetadata(
        icon="📝",
        gradient="from-purple-500 to-indigo-500",
        accent_color="#7c3aed",
        category="CONTENT",
        description="Flagship Content Writer and copy editor.",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    )
)
