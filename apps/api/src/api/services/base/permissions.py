"""
EAIMOS Enterprise Permission Matrix & Enums
===========================================
Defines granular enterprise permissions across all 15 system domains and
provides default role-to-permission mapping matrices for RBAC/ABAC authorization.
"""

from enum import Enum
from typing import Dict, Set


class EnterprisePermission(str, Enum):
    """System-wide granular enterprise permissions."""

    # IAM & Platform (Sprint 1 & 2)
    IAM_USER_READ = "iam:user:read"
    IAM_USER_WRITE = "iam:user:write"
    IAM_USER_DELETE = "iam:user:delete"
    IAM_ROLE_MANAGE = "iam:role:manage"
    IAM_ORG_READ = "iam:org:read"
    IAM_ORG_WRITE = "iam:org:write"
    IAM_SESSION_MANAGE = "iam:session:manage"

    # AI Gateway (Sprint 3)
    AI_REQUEST_CREATE = "ai:request:create"
    AI_REQUEST_READ = "ai:request:read"
    AI_PROVIDER_MANAGE = "ai:provider:manage"
    AI_ROUTING_WRITE = "ai:routing:write"

    # Prompt Platform (Sprint 4)
    PROMPT_CREATE = "prompt:create"
    PROMPT_READ = "prompt:read"
    PROMPT_UPDATE = "prompt:update"
    PROMPT_DELETE = "prompt:delete"
    PROMPT_PUBLISH = "prompt:publish"
    PROMPT_EVALUATE = "prompt:evaluate"

    # Knowledge Platform (Sprint 5)
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_INDEX = "knowledge:index"
    KNOWLEDGE_DELETE = "knowledge:delete"

    # AI Agents (Sprint 6)
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_EXECUTE = "agent:execute"
    AGENT_MANAGE = "agent:manage"

    # Workflow Engine (Sprint 7)
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_DELETE = "workflow:delete"

    # Marketing Platform (Sprint 8)
    MARKETING_CAMPAIGN_READ = "marketing:campaign:read"
    MARKETING_CAMPAIGN_WRITE = "marketing:campaign:write"
    MARKETING_CAMPAIGN_LAUNCH = "marketing:campaign:launch"

    # CRM (Sprint 9)
    CRM_DEAL_READ = "crm:deal:read"
    CRM_DEAL_WRITE = "crm:deal:write"
    CRM_CONTACT_READ = "crm:contact:read"
    CRM_CONTACT_WRITE = "crm:contact:write"

    # Integrations (Sprint 10)
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"

    # Notifications (Sprint 11)
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_SEND = "notification:send"

    # Billing (Sprint 12)
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"

    # Analytics (Sprint 13)
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"

    # Security & Audit (Sprint 14)
    SECURITY_AUDIT_READ = "security:audit:read"
    SECURITY_POLICY_MANAGE = "security:policy:manage"

    # Administration (Sprint 15)
    ADMIN_SYSTEM = "admin:system"


# Default RBAC Role to Permission Mapping
DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "super_admin": {"*:*"},
    "system_admin": {"*:*"},
    "organization_admin": {
        EnterprisePermission.IAM_USER_READ.value,
        EnterprisePermission.IAM_USER_WRITE.value,
        EnterprisePermission.IAM_USER_DELETE.value,
        EnterprisePermission.IAM_ROLE_MANAGE.value,
        EnterprisePermission.IAM_ORG_READ.value,
        EnterprisePermission.IAM_ORG_WRITE.value,
        EnterprisePermission.AI_REQUEST_CREATE.value,
        EnterprisePermission.AI_REQUEST_READ.value,
        EnterprisePermission.PROMPT_CREATE.value,
        EnterprisePermission.PROMPT_READ.value,
        EnterprisePermission.PROMPT_UPDATE.value,
        EnterprisePermission.PROMPT_DELETE.value,
        EnterprisePermission.PROMPT_PUBLISH.value,
        EnterprisePermission.KNOWLEDGE_READ.value,
        EnterprisePermission.KNOWLEDGE_WRITE.value,
        EnterprisePermission.AGENT_CREATE.value,
        EnterprisePermission.AGENT_READ.value,
        EnterprisePermission.AGENT_EXECUTE.value,
        EnterprisePermission.WORKFLOW_READ.value,
        EnterprisePermission.WORKFLOW_WRITE.value,
        EnterprisePermission.WORKFLOW_EXECUTE.value,
        EnterprisePermission.MARKETING_CAMPAIGN_READ.value,
        EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value,
        EnterprisePermission.MARKETING_CAMPAIGN_LAUNCH.value,
        EnterprisePermission.CRM_DEAL_READ.value,
        EnterprisePermission.CRM_DEAL_WRITE.value,
        EnterprisePermission.INTEGRATION_READ.value,
        EnterprisePermission.INTEGRATION_WRITE.value,
        EnterprisePermission.NOTIFICATION_READ.value,
        EnterprisePermission.NOTIFICATION_SEND.value,
        EnterprisePermission.BILLING_READ.value,
        EnterprisePermission.BILLING_MANAGE.value,
        EnterprisePermission.ANALYTICS_READ.value,
        EnterprisePermission.SECURITY_AUDIT_READ.value,
    },
    "marketer": {
        EnterprisePermission.PROMPT_READ.value,
        EnterprisePermission.PROMPT_CREATE.value,
        EnterprisePermission.KNOWLEDGE_READ.value,
        EnterprisePermission.AGENT_READ.value,
        EnterprisePermission.AGENT_EXECUTE.value,
        EnterprisePermission.WORKFLOW_READ.value,
        EnterprisePermission.WORKFLOW_EXECUTE.value,
        EnterprisePermission.MARKETING_CAMPAIGN_READ.value,
        EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value,
        EnterprisePermission.MARKETING_CAMPAIGN_LAUNCH.value,
        EnterprisePermission.CRM_DEAL_READ.value,
        EnterprisePermission.CRM_CONTACT_READ.value,
        EnterprisePermission.ANALYTICS_READ.value,
    },
    "developer": {
        EnterprisePermission.AI_REQUEST_CREATE.value,
        EnterprisePermission.AI_REQUEST_READ.value,
        EnterprisePermission.PROMPT_CREATE.value,
        EnterprisePermission.PROMPT_READ.value,
        EnterprisePermission.PROMPT_UPDATE.value,
        EnterprisePermission.PROMPT_PUBLISH.value,
        EnterprisePermission.KNOWLEDGE_READ.value,
        EnterprisePermission.KNOWLEDGE_WRITE.value,
        EnterprisePermission.AGENT_CREATE.value,
        EnterprisePermission.AGENT_READ.value,
        EnterprisePermission.AGENT_EXECUTE.value,
        EnterprisePermission.WORKFLOW_READ.value,
        EnterprisePermission.WORKFLOW_WRITE.value,
        EnterprisePermission.INTEGRATION_READ.value,
        EnterprisePermission.INTEGRATION_WRITE.value,
    },
    "viewer": {
        EnterprisePermission.IAM_ORG_READ.value,
        EnterprisePermission.PROMPT_READ.value,
        EnterprisePermission.KNOWLEDGE_READ.value,
        EnterprisePermission.AGENT_READ.value,
        EnterprisePermission.WORKFLOW_READ.value,
        EnterprisePermission.MARKETING_CAMPAIGN_READ.value,
        EnterprisePermission.CRM_DEAL_READ.value,
        EnterprisePermission.ANALYTICS_READ.value,
    },
}
