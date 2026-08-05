from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

RESEARCH_AGENT_MANIFEST = AgentManifest(
    id="RESEARCH",
    name="Research Agent",
    description="Competitor research, SWOT analysis, and industry trends",
    version="1.0.0",
    category="RESEARCH",
    tags=["marketing", "research"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['RESEARCH', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['web_search_tool', 'knowledge_tool', 'calculator_tool'],
    required_permissions=["manage_research"],
    default_prompt="You are an expert market analyst. You compile competitor profiles, SWOT analysis matrices, pricing grids, customer persona surveys, and trends.",
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
        allowed_tools=['web_search_tool', 'knowledge_tool', 'calculator_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="RESEARCH",
        description="Competitor research, SWOT analysis, and industry trends",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="session",
    planner_strategy="reactive",
    evaluation_strategy="research"
)
