from api.database.base import Base
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, OrganizationInvitation, OrganizationSettings
from api.models.auth import Role, Permission, RefreshToken, AuditLog
from api.models.email_verification import EmailVerificationToken
from api.models.email_log import EmailLog
from api.models.iam import (
    UserSession, PasswordResetToken, APIKey, OAuthProvider, OAuthAccount, SecurityPolicy,
    role_permissions_junction, UserRole
)
from api.models.company import Company
from api.models.contact import Contact
from api.models.lead import Lead, LeadStatus
from api.models.activity import Activity, ActivityType
from api.models.prompt import (
    Prompt, PromptCollection, PromptFolder, PromptComment,
    PromptTestCase, PromptEvaluation, PromptExecution
)
from api.models.prompt_abtests import PromptABTest, PromptABTestResult
from api.models.conversation import Conversation
from api.models.message import Message
from api.models.chat_attachment import ChatAttachment
from api.models.chat_participant import ChatParticipant
from api.models.conversation_bookmark import ConversationBookmark
from api.models.conversation_share import ConversationShare
from api.models.content_generator import GeneratedContent
from api.models.content_variant import ContentVariant
from api.models.campaign import Campaign, CampaignTemplate, CampaignAnalytics, CampaignStatus, CampaignChannel
from api.models.campaign_audiences import CampaignAudience, CampaignEvent, EmailSend
from api.models.deals import Pipeline, DealStage, Deal, EmailSubscription, ContactCustomField, ContactCustomValue
from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.models.ai_platform import (
    AIProvider, AIModel, AIProviderKey, AIProviderHealth,
    AIRequest, AIUsage, AICost, AIPlaygroundSession, AIPlaygroundMessage,
    AIOrgLimit
)
from api.models.knowledge import (
    KnowledgeDocument, DocumentChunk, KnowledgeCollection, KnowledgeFolder,
    KnowledgeDocumentVersion, KnowledgeProcessingJob, KnowledgeSearchHistory,
    KnowledgeSavedSearch, KnowledgePermission, DocumentChunkEmbedding, KnowledgeRetrievalLog
)
from api.models.file_asset import FileAsset
# Phase 2 — AI Agent Platform
from api.models.agent import (
    AgentDefinition, AgentSession, AgentRun, AgentLog,
    AgentType, AgentStatus, AgentRunStatus
)
from api.models.agent_tools import (
    AgentTool, AgentToolExecution, AgentKnowledgeBinding, AgentAnalytics
)
from api.ai.agents.image.history import AIImageLibrary, AIImageCollection
# Phase 3 — Agent Memory System
from api.models.memory import (
    AgentMemory, ConversationMemory, OrganizationMemory, MemoryType
)
# Phase 4 — Workflow Engine
from api.models.workflow import (
    WorkflowDefinition, WorkflowExecution, WorkflowStep,
    WorkflowTrigger, WorkflowStatus, ExecutionStatus,
    WorkflowVersion, WorkflowTriggerEntity, WorkflowSchedule, WorkflowAnalytics
)
# Phase 5 — Integration & Notification Platform
from api.models.integration import (
    Integration, IntegrationCredential, SyncJob,
    IntegrationProvider, IntegrationStatus,
    Notification, NotificationPreference,
    NotificationChannel, NotificationPriority
)
from api.models.integration_webhooks import (
    WebhookEndpoint, WebhookEvent, WebhookDelivery, IntegrationFieldMapping, IntegrationSyncLog
)
from api.models.notification_templates import (
    NotificationTemplate, NotificationBatch, NotificationDelivery as BatchNotificationDelivery, NotificationDigest
)
from api.models.billing import (
    BillingPlan, PlanFeature, Subscription, PaymentMethod, Invoice, InvoiceLineItem, Payment, Credit,
    CreditTransaction, UsageRecord, BillingAlert, PromoCode, PromoCodeRedemption
)
from api.models.analytics import (
    AnalyticsSnapshot, AnalyticsDashboard, AnalyticsWidget, AnalyticsReport, AnalyticsReportRun,
    AnalyticsEvent, AnalyticsFunnel, AnalyticsFunnelStep, AnalyticsCohort
)
from api.models.security_platform import (
    SecurityIncident, ThreatDetection, ComplianceFramework, ComplianceControl, ComplianceAssessment,
    DataClassificationRule, PiiScanResult, SecurityAlert, IpAllowlist, SecurityEventLog
)
from api.models.admin import (
    SystemConfiguration, SupportTicket, SupportTicketMessage, ImpersonationLog, MaintenanceWindow,
    PlatformAnnouncement, AdminActionLog, SystemHealthSnapshot, RateLimitOverride
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
    "Base", "User", "Organization", "UserOrganization", "UserRole", "OrganizationInvitation", "OrganizationSettings",
    "Role", "Permission", "RefreshToken", "AuditLog",
    "EmailVerificationToken",
    "EmailLog",
    # CRM
    "Company", "Contact", "Lead", "LeadStatus", "Activity", "ActivityType",
    "Pipeline", "DealStage", "Deal", "EmailSubscription", "ContactCustomField", "ContactCustomValue",
    # AI Platform
    "Prompt", "PromptCollection", "PromptFolder", "PromptComment",
    "PromptTestCase", "PromptEvaluation", "PromptExecution",
    "PromptABTest", "PromptABTestResult",
    "Conversation", "Message", "ChatAttachment", "ChatParticipant",
    "ConversationBookmark", "ConversationShare",
    "GeneratedContent", "ContentVariant",
    "AIModelRegistry", "AIRoutingRule", "AITokenUsage",
    "AIProvider", "AIModel", "AIProviderKey", "AIProviderHealth",
    "AIRequest", "AIUsage", "AICost", "AIPlaygroundSession", "AIPlaygroundMessage",
    "AIOrgLimit",
    "KnowledgeDocument", "DocumentChunk", "KnowledgeCollection", "KnowledgeFolder",
    "KnowledgeDocumentVersion", "KnowledgeProcessingJob", "KnowledgeSearchHistory",
    "KnowledgeSavedSearch", "KnowledgePermission", "DocumentChunkEmbedding", "KnowledgeRetrievalLog",
    # Campaigns
    "Campaign", "CampaignTemplate", "CampaignAnalytics",
    "CampaignStatus", "CampaignChannel",
    "CampaignAudience", "CampaignEvent", "EmailSend",
    # Files
    "FileAsset",
    # Phase 2: Agents
    "AgentDefinition", "AgentSession", "AgentRun", "AgentLog",
    "AgentType", "AgentStatus", "AgentRunStatus",
    "AgentTool", "AgentToolExecution", "AgentKnowledgeBinding", "AgentAnalytics",
    "AIImageLibrary", "AIImageCollection",
    # Phase 3: Memory
    "AgentMemory", "ConversationMemory", "OrganizationMemory", "MemoryType",
    # Phase 4: Workflow
    "WorkflowDefinition", "WorkflowExecution", "WorkflowStep",
    "WorkflowTrigger", "WorkflowStatus", "ExecutionStatus",
    "WorkflowVersion", "WorkflowTriggerEntity", "WorkflowSchedule", "WorkflowAnalytics",
    # Phase 5: Integrations & Notifications
    "Integration", "IntegrationCredential", "SyncJob",
    "IntegrationProvider", "IntegrationStatus",
    "Notification", "NotificationPreference",
    "NotificationChannel", "NotificationPriority",
    "WebhookEndpoint", "WebhookEvent", "WebhookDelivery", "IntegrationFieldMapping", "IntegrationSyncLog",
    "NotificationTemplate", "NotificationBatch", "BatchNotificationDelivery", "NotificationDigest",
    # Billing
    "BillingPlan", "PlanFeature", "Subscription", "PaymentMethod", "Invoice", "InvoiceLineItem",
    "Payment", "Credit", "CreditTransaction", "UsageRecord", "BillingAlert", "PromoCode", "PromoCodeRedemption",
    # Analytics
    "AnalyticsSnapshot", "AnalyticsDashboard", "AnalyticsWidget", "AnalyticsReport", "AnalyticsReportRun",
    "AnalyticsEvent", "AnalyticsFunnel", "AnalyticsFunnelStep", "AnalyticsCohort",
    # Security
    "SecurityIncident", "ThreatDetection", "ComplianceFramework", "ComplianceControl", "ComplianceAssessment",
    "DataClassificationRule", "PiiScanResult", "SecurityAlert", "IpAllowlist", "SecurityEventLog",
    # Admin
    "SystemConfiguration", "SupportTicket", "SupportTicketMessage", "ImpersonationLog", "MaintenanceWindow",
    "PlatformAnnouncement", "AdminActionLog", "SystemHealthSnapshot", "RateLimitOverride",
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
