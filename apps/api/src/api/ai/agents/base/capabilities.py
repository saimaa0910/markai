from enum import Enum

class AgentCapability(str, Enum):
    CONTENT = "CONTENT"
    SEO = "SEO"
    RESEARCH = "RESEARCH"
    CAMPAIGN = "CAMPAIGN"
    ANALYTICS = "ANALYTICS"
    BRAND = "BRAND"
    WORKFLOW = "WORKFLOW"
    REPORTING = "REPORTING"
    RAG = "RAG"
    TOOLS = "TOOLS"
    IMAGE = "IMAGE"
    EMAIL = "EMAIL"
    SOCIAL = "SOCIAL"
    CRM = "CRM"
    AUTOMATION = "AUTOMATION"
