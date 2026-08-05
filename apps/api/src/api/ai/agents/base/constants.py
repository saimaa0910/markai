import enum

class AgentCategory(str, enum.Enum):
    MARKETING = "MARKETING"
    CONTENT = "CONTENT"
    CAMPAIGN = "CAMPAIGN"
    CRM = "CRM"
    ANALYTICS = "ANALYTICS"
    RESEARCH = "RESEARCH"
    SEO = "SEO"
    WORKFLOW = "WORKFLOW"
    SYSTEM = "SYSTEM"

class AgentStatus(str, enum.Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
