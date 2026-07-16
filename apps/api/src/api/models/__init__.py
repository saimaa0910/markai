from api.database.base import Base
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole, OrganizationInvitation
from api.models.auth import Role, Permission, RefreshToken, AuditLog
from api.models.company import Company
from api.models.contact import Contact
from api.models.lead import Lead, LeadStatus
from api.models.activity import Activity, ActivityType
from api.models.prompt import Prompt
from api.models.conversation import Conversation
from api.models.message import Message
from api.models.chat_attachment import ChatAttachment
from api.models.chat_participant import ChatParticipant
from api.models.content_generator import GeneratedContent
from api.models.content_variant import ContentVariant
from api.models.campaign import Campaign, CampaignTemplate, CampaignAnalytics, CampaignStatus, CampaignChannel
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.models.ai_platform import (
    AIProvider, AIModel, AIProviderKey, AIProviderHealth,
    AIRequest, AIUsage, AICost, AIPlaygroundSession, AIPlaygroundMessage,
    AIOrgLimit
)
from api.models.knowledge import KnowledgeDocument, DocumentChunk
from api.models.file_asset import FileAsset
# Phase 2 — AI Agent Platform
from api.models.agent import (
    AgentDefinition, AgentSession, AgentRun, AgentLog,
    AgentType, AgentStatus, AgentRunStatus
)
# Phase 3 — Agent Memory System
from api.models.memory import (
    AgentMemory, ConversationMemory, OrganizationMemory, MemoryType
)
# Phase 4 — Workflow Engine
from api.models.workflow import (
    WorkflowDefinition, WorkflowExecution, WorkflowStep,
    WorkflowTrigger, WorkflowStatus, ExecutionStatus
)
# Phase 5 — Integration & Notification Platform
from api.models.integration import (
    Integration, IntegrationCredential, SyncJob,
    IntegrationProvider, IntegrationStatus,
    Notification, NotificationPreference,
    NotificationChannel, NotificationPriority
)
# Phase 1A — Infrastructure
from api.models.infrastructure import (
    AIBackgroundJob, AIJobHistory, AICacheMetadata,
    AIQueueMessage, AISchedulerHistory, AIWorkerMetric
)
# Phase 1B — Router
from api.models.router import (
    AIRoutingPolicy, AIRoutingLog, AIFailoverEvent
)
# Phase 1C — Security & Governance
from api.models.security import (
    AISecurityPolicyRule, AISecurityEvent, AIScanLog, AIQuotaUsage
)
# Phase 1D — Observability
from api.models.observability import (
    AITrace, AILog, AIIncident, AIAlert, AIPerformanceMetric
)

__all__ = [
    # Foundation
    "Base", "User", "Organization", "UserOrganization", "UserRole", "OrganizationInvitation",
    "Role", "Permission", "RefreshToken", "AuditLog",
    # CRM
    "Company", "Contact", "Lead", "LeadStatus", "Activity", "ActivityType",
    # AI Platform
    "Prompt", "Conversation", "Message", "ChatAttachment", "ChatParticipant",
    "GeneratedContent", "ContentVariant",
    "AIModelRegistry", "AIRoutingRule", "AITokenUsage",
    "AIProvider", "AIModel", "AIProviderKey", "AIProviderHealth",
    "AIRequest", "AIUsage", "AICost", "AIPlaygroundSession", "AIPlaygroundMessage",
    "AIOrgLimit",
    "KnowledgeDocument", "DocumentChunk",
    # Campaigns
    "Campaign", "CampaignTemplate", "CampaignAnalytics",
    "CampaignStatus", "CampaignChannel",
    # Files
    "FileAsset",
    # Phase 2: Agents
    "AgentDefinition", "AgentSession", "AgentRun", "AgentLog",
    "AgentType", "AgentStatus", "AgentRunStatus",
    # Phase 3: Memory
    "AgentMemory", "ConversationMemory", "OrganizationMemory", "MemoryType",
    # Phase 4: Workflow
    "WorkflowDefinition", "WorkflowExecution", "WorkflowStep",
    "WorkflowTrigger", "WorkflowStatus", "ExecutionStatus",
    # Phase 5: Integrations & Notifications
    "Integration", "IntegrationCredential", "SyncJob",
    "IntegrationProvider", "IntegrationStatus",
    "Notification", "NotificationPreference",
    "NotificationChannel", "NotificationPriority",
    # Phase 1A: Infrastructure
    "AIBackgroundJob", "AIJobHistory", "AICacheMetadata",
    "AIQueueMessage", "AISchedulerHistory", "AIWorkerMetric",
    # Phase 1B: Router
    "AIRoutingPolicy", "AIRoutingLog", "AIFailoverEvent",
    # Phase 1C: Security
    "AISecurityPolicyRule", "AISecurityEvent", "AIScanLog", "AIQuotaUsage",
    # Phase 1D: Observability
    "AITrace", "AILog", "AIIncident", "AIAlert", "AIPerformanceMetric",
]
