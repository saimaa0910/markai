from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

BRAND_AGENT_MANIFEST = AgentManifest(
    id="BRAND",
    name="Brand Agent",
    description="Brand voice checker, tone regulator, and style compliance auditor",
    version="1.0.0",
    category="CRM",
    tags=["marketing", "brand"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['BRAND', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['knowledge_tool'],
    required_permissions=["manage_brand"],
    default_prompt="You are a brand editor. You review all copy, flag prohibited expressions, check style rules, and grade text voice compliance.",
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
        allowed_tools=['knowledge_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="CRM",
        description="Brand voice checker, tone regulator, and style compliance auditor",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="knowledge",
    planner_strategy="reactive",
    evaluation_strategy="brand"
)
