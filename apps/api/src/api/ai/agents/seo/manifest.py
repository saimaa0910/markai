from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

SEO_AGENT_MANIFEST = AgentManifest(
    id="SEO",
    name="SEO Agent",
    description="SERP rank tracking, technical audit, keyword clusters",
    version="1.0.0",
    category="SEO",
    tags=["marketing", "seo"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['SEO', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['web_search_tool', 'knowledge_tool', 'analytics_tool'],
    required_permissions=["manage_seo"],
    default_prompt="You are an expert SEO Agent. You analyze site structure, rank signals, keyword density, internal linking recommendations, and competitive gaps.",
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
        allowed_tools=['web_search_tool', 'knowledge_tool', 'analytics_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="SEO",
        description="SERP rank tracking, technical audit, keyword clusters",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="window",
    planner_strategy="sequential",
    evaluation_strategy="seo"
)
