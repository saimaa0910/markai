from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus
from api.ai.agents.image.constants import DEFAULT_PROVIDER_PRIORITY, SUPPORTED_MODELS

IMAGE_AGENT_MANIFEST = AgentManifest(
    id="IMAGE",
    name="Image Studio Agent",
    description="Enterprise marketing creative layout designer, photo variation editor, brand mockup illustrator",
    version="1.0.0",
    category="IMAGE",
    tags=["marketing", "creative", "design"],
    icon="🎨",
    color="#8b5cf6",  # Violet
    owner="Viptant",
    visibility="public",
    capabilities=["IMAGE", "RAG", "TOOLS"],
    supported_providers=DEFAULT_PROVIDER_PRIORITY,
    supported_models=SUPPORTED_MODELS,
    supported_tools=["image_generate_tool", "image_edit_tool", "image_upscale_tool"],
    required_permissions=["manage_images"],
    default_prompt="You are a principal creative advertising designer. You craft gorgeous image generation descriptions that embed brand guidelines, campaign context, color palettes, and typographic accents.",
    default_model="flux-schnell",
    default_temperature=0.7,
    policies=AgentPolicies(
        allowed_models=SUPPORTED_MODELS,
        allowed_providers=DEFAULT_PROVIDER_PRIORITY,
        temperature=0.7,
        max_cost=25.0,
        max_runtime_sec=600,
        max_iterations=15,
    ),
    permissions=AgentPermissions(
        allowed_tools=["image_generate_tool", "image_edit_tool", "image_upscale_tool"]
    ),
    metadata=AgentMetadata(
        icon="🎨",
        gradient="from-violet-500 to-fuchsia-500",
        accent_color="#8b5cf6",
        category="IMAGE",
        description="Enterprise marketing creative layout designer, photo variation editor, brand mockup illustrator",
        author="Viptant",
        version="1.0.0",
        status=AgentStatus.STABLE
    ),
    memory_strategy="window",
    planner_strategy="sequential",
    evaluation_strategy="image"
)
