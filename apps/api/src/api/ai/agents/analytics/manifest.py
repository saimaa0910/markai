from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

ANALYTICS_AGENT_MANIFEST = AgentManifest(
    id="ANALYTICS",
    name="Analytics Agent",
    description="KPI forecast analyzer, ROI models, and anomaly tracker",
    version="1.0.0",
    category="ANALYTICS",
    tags=["marketing", "analytics"],
    icon="🤖",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=['ANALYTICS', 'TOOLS'],
    supported_providers=["openai", "google", "groq"],
    supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
    supported_tools=['analytics_tool', 'calculator_tool'],
    required_permissions=["manage_analytics"],
    default_prompt="You are a principal marketing analyst. You forecast conversion funnels, calculate ROI matrices, alert on spend anomalies, and advise budget distributions.",
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
        allowed_tools=['analytics_tool', 'calculator_tool']
    ),
    metadata=AgentMetadata(
        icon="🤖",
        gradient="from-cyan-500 to-blue-500",
        accent_color="#0ea5e9",
        category="ANALYTICS",
        description="KPI forecast analyzer, ROI models, and anomaly tracker",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="organization",
    planner_strategy="reflective",
    evaluation_strategy="analytics"
)
