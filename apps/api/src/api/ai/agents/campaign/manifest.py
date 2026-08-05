from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

CAMPAIGN_AGENT_MANIFEST = AgentManifest(
    id="CAMPAIGN",
    name="Campaign Agent",
    description="Multi-channel planner, budget dispatcher, and A/B creative coordinator",
    version="1.0.0",
    category="CAMPAIGN",
    tags=["marketing", "campaign"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['CAMPAIGN', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['knowledge_tool', 'crm_tool', 'email_tool', 'analytics_tool'],
    required_permissions=["manage_campaign"],
    default_prompt="You are a campaign director. You design target segments, distribute budgets, construct A/B variants, and coordinate copy variations.",
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
        allowed_tools=['knowledge_tool', 'crm_tool', 'email_tool', 'analytics_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="CAMPAIGN",
        description="Multi-channel planner, budget dispatcher, and A/B creative coordinator",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="hybrid",
    planner_strategy="hierarchical",
    evaluation_strategy="campaign"
)
