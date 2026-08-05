"""
Social Agent Manifest — Sprint 7.5
====================================
Defines SOCIAL_AGENT_MANIFEST with full capability declarations,
provider policy, and tool permission set.
"""
from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus
from api.ai.agents.social.constants import DEFAULT_PROVIDER_PRIORITY, SUPPORTED_MODELS

SOCIAL_AGENT_MANIFEST = AgentManifest(
    id="SOCIAL",
    name="Enterprise Social Media Agent",
    description=(
        "Full-lifecycle social media agent: plans, generates, images, "
        "schedules, publishes, monitors, and optimizes posts across 14 platforms."
    ),
    version="1.0.0",
    category="SOCIAL",
    tags=["social", "marketing", "content", "scheduling", "publishing", "analytics"],
    icon="📲",
    color="#0ea5e9",
    owner="Viptant",
    visibility="public",
    capabilities=[
        "SOCIAL",
        "CONTENT",
        "IMAGE",
        "CAMPAIGN",
        "BRAND",
        "ANALYTICS",
        "WORKFLOW",
        "MEMORY",
        "TOOLS",
        "STREAMING",
    ],
    supported_providers=DEFAULT_PROVIDER_PRIORITY,
    supported_models=SUPPORTED_MODELS,
    supported_tools=[
        "knowledge_tool",
        "image_generation_tool",
        "campaign_tool",
        "analytics_tool",
        "brand_tool",
        "web_search_tool",
        "email_tool",
        "calendar_tool",
    ],
    required_permissions=["manage_social"],
    default_prompt=(
        "You are a principal enterprise social media strategist with deep expertise "
        "in platform-specific content optimization, brand voice compliance, hashtag "
        "strategy, viral content mechanics, and data-driven publishing calendars. "
        "You orchestrate content creation, image generation, scheduling, and analytics "
        "to maximize engagement and brand impact across all major social platforms."
    ),
    default_model="gemini-1.5-flash",
    default_temperature=0.75,
    policies=AgentPolicies(
        allowed_models=SUPPORTED_MODELS,
        allowed_providers=DEFAULT_PROVIDER_PRIORITY,
        temperature=0.75,
        max_cost=25.0,
        max_runtime_sec=600,
        max_iterations=20,
    ),
    permissions=AgentPermissions(
        allowed_tools=[
            "knowledge_tool",
            "image_generation_tool",
            "campaign_tool",
            "analytics_tool",
            "brand_tool",
            "web_search_tool",
            "email_tool",
            "calendar_tool",
        ]
    ),
    metadata=AgentMetadata(
        icon="📲",
        gradient="from-sky-500 to-cyan-500",
        accent_color="#0ea5e9",
        category="SOCIAL",
        description=(
            "Full-lifecycle social media agent: plans, generates, images, "
            "schedules, publishes, monitors, and optimizes posts across 14 platforms."
        ),
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE,
    ),
    memory_strategy="window",
    planner_strategy="sequential",
    evaluation_strategy="social",
    streaming_support=True,
    reflection_support=True,
    evaluation_support=True,
    telemetry_support=True,
)
