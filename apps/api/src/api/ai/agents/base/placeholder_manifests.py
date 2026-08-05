from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

def create_placeholder_manifest(agent_id: str, name: str, desc: str, category: str, default_prompt: str, tools: list) -> AgentManifest:
    return AgentManifest(
        id=agent_id,
        name=name,
        description=desc,
        version="1.0.0",
        category=category,
        tags=["marketing", category.lower()],
        icon="🤖",
        color="#0ea5e9",
        owner="Viptant",
        visibility="public",
        capabilities=[category, "RAG", "TOOLS"],
        supported_providers=["openai", "google"],
        supported_models=["gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"],
        supported_tools=tools,
        required_permissions=[f"manage_{category.lower()}"],
        default_prompt=default_prompt,
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
            allowed_tools=tools
        ),
        metadata=AgentMetadata(
            icon="🤖",
            gradient="from-cyan-500 to-blue-500",
            accent_color="#0ea5e9",
            category=category,
            description=desc,
            author="Viptant",
            version="1.0.0",
            status=AgentStatus.EXPERIMENTAL
        )
    )

PLACEHOLDERS = [
    create_placeholder_manifest(
        "SEO", "SEO Agent",
        "SERP rank tracking, technical audit, keyword clusters",
        "SEO",
        "You are an expert SEO Agent. You analyze site structure, rank signals, keyword density, internal linking recommendations, and competitive gaps.",
        ["web_search_tool", "knowledge_tool", "analytics_tool"]
    ),
    create_placeholder_manifest(
        "RESEARCH", "Research Agent",
        "Competitor research, SWOT analysis, and industry trends",
        "RESEARCH",
        "You are an expert market analyst. You compile competitor profiles, SWOT analysis matrices, pricing grids, customer persona surveys, and trends.",
        ["web_search_tool", "knowledge_tool", "calculator_tool"]
    ),
    create_placeholder_manifest(
        "CAMPAIGN", "Campaign Agent",
        "Multi-channel planner, budget dispatcher, and A/B creative coordinator",
        "CAMPAIGN",
        "You are a campaign director. You design target segments, distribute budgets, construct A/B variants, and coordinate copy variations.",
        ["knowledge_tool", "crm_tool", "email_tool", "analytics_tool"]
    ),
    create_placeholder_manifest(
        "ANALYTICS", "Analytics Agent",
        "KPI forecast analyzer, ROI models, and anomaly tracker",
        "ANALYTICS",
        "You are a principal marketing analyst. You forecast conversion funnels, calculate ROI matrices, alert on spend anomalies, and advise budget distributions.",
        ["analytics_tool", "calculator_tool"]
    ),
    create_placeholder_manifest(
        "BRAND", "Brand Agent",
        "Brand voice checker, tone regulator, and style compliance auditor",
        "CRM", # Maps category to CRM or CUSTOM
        "You are a brand editor. You review all copy, flag prohibited expressions, check style rules, and grade text voice compliance.",
        ["knowledge_tool"]
    ),
    create_placeholder_manifest(
        "WORKFLOW", "Workflow Agent",
        "No-code automation planner, event triggers scheduler, and handler retry policy engine",
        "WORKFLOW",
        "You are an automation coordinator. You build task execution chains, schedule trigger sequences, handle conditional branching, and resolve tool execution errors.",
        ["workflow_tool"]
    ),
    create_placeholder_manifest(
        "MANAGER", "Manager Agent",
        "Multi-agent workflow supervisor, task dispatcher, and response evaluator",
        "CRM",
        "You are a team coordinator. You decompose complex marketing goals, delegate tasks to sub-agents, monitor logs, and synthesise executive reports.",
        ["knowledge_tool", "workflow_tool"]
    ),
    create_placeholder_manifest(
        "SALES", "Sales Agent",
        "CRM lead tracker, client contact manager, and activity logger",
        "SALES",
        "You are a sales specialist. You monitor pipelines, update leads, log actions, and drafts contact messages.",
        ["crm_tool", "email_tool"]
    ),
    create_placeholder_manifest(
        "SUPPORT", "Support Agent",
        "Client issues responder and query handler",
        "SUPPORT",
        "You are a customer support agent. You handle product FAQs, trace details, drafts responses, and resolve support queries.",
        ["knowledge_tool"]
    ),
    create_placeholder_manifest(
        "EMAIL", "Email Agent",
        "Automated outbound campaign writer",
        "CRM",
        "You are an email copywriter. You draft cold outreach templates, sequence layouts, subject options, and personalized copy.",
        ["email_tool", "knowledge_tool"]
    ),
    create_placeholder_manifest(
        "SOCIAL", "Social Agent",
        "Social networks writer and scheduler",
        "CRM",
        "You are a social content specialist. You draft posts, optimize character counts, add hashtags, and adapt copy.",
        ["web_search_tool", "knowledge_tool"]
    ),
]
