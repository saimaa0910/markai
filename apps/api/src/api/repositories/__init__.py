"""
EAIMOS Enterprise Repository Layer (Sprints 1–15)
=================================================
The Repository Layer is the ONLY layer allowed to communicate directly with SQLAlchemy ORM.
No service, API, worker, or AI module may directly access SQLAlchemy.
"""

from api.repositories.exceptions import (
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    OptimisticLockError,
    TenantViolationError,
    DatabaseConstraintError,
)
from api.repositories.pagination import (
    OffsetParams,
    CursorParams,
    PageResult,
    CursorResult,
)
from api.repositories.filters import (
    FilterParam,
    FilterOperator,
    apply_filters,
)
from api.repositories.sorting import (
    SortParam,
    SortDirection,
    apply_sorting,
)
from api.repositories.query_builder import QueryOptions
from api.repositories.interfaces import (
    IBaseRepository,
    ITenantRepository,
    IAuditRepository,
    ISearchRepository,
)
from api.repositories.base import BaseRepository
from api.repositories.tenant import TenantRepository
from api.repositories.audit import AuditRepository
from api.repositories.search import SearchRepository
from api.repositories.unit_of_work import UnitOfWork

# Concrete Sprint Repositories
from api.repositories.organization_repository import OrganizationRepository
from api.repositories.user_repository import UserRepository
from api.repositories.membership_repository import UserOrganizationRepository
from api.repositories.system_config_repository import SystemConfigRepository
from api.repositories.audit_log_repository import AuditLogRepository
from api.repositories.iam_repository import (
    UserSessionRepository,
    APIKeyRepository,
    PasswordResetTokenRepository,
    OAuthAccountRepository,
    OrganizationInvitationRepository,
)
from api.repositories.ai_gateway_repository import (
    AIProviderRepository,
    AIModelRepository,
    AIRequestRepository,
    AITokenUsageRepository,
    AIRoutingPolicyRepository,
)
from api.repositories.prompt_platform_repository import (
    EnterprisePromptRepository,
    EnterprisePromptCollectionRepository,
    EnterprisePromptFolderRepository,
    PromptTestCaseRepository,
    PromptEvaluationRepository,
    PromptABTestRepository,
)
from api.repositories.knowledge_platform_repository import (
    KnowledgeDocumentRepository,
    DocumentChunkRepository,
    KnowledgeCollectionRepository,
    KnowledgeFolderRepository,
    KnowledgeProcessingJobRepository,
    FileAssetRepository,
)
from api.repositories.agent_platform_repository import (
    EnterpriseAgentDefinitionRepository,
    AgentSessionRepository,
    AgentRunRepository,
    AgentToolRepository,
    AgentMemoryRepository,
)
from api.repositories.workflow_repository import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowStepRepository,
    WorkflowTriggerRepository,
)
from api.repositories.marketing_repository import (
    EnterpriseCampaignRepository,
    CampaignTemplateRepository,
    CampaignAudienceRepository,
    GeneratedContentRepository,
)
from api.repositories.crm_repository import (
    CompanyRepository,
    ContactRepository,
    LeadRepository,
    ActivityRepository,
    DealRepository,
)
from api.repositories.integration_repository import (
    IntegrationRepository,
    IntegrationCredentialRepository,
    SyncJobRepository,
    WebhookEndpointRepository,
    WebhookDeliveryRepository,
)
from api.repositories.notification_repository import (
    NotificationRepository,
    NotificationPreferenceRepository,
    NotificationTemplateRepository,
)
from api.repositories.billing_repository import (
    BillingPlanRepository,
    SubscriptionRepository,
    InvoiceRepository,
    PaymentRepository,
    CreditRepository,
    UsageRecordRepository,
)
from api.repositories.analytics_repository import (
    AnalyticsDashboardRepository,
    AnalyticsWidgetRepository,
    AnalyticsReportRepository,
    AnalyticsEventRepository,
    AnalyticsSnapshotRepository,
)
from api.repositories.security_repository import (
    SecurityIncidentRepository,
    ThreatDetectionRepository,
    ComplianceAssessmentRepository,
    PiiScanResultRepository,
    SecurityEventLogRepository,
)
from api.repositories.admin_repository import (
    SupportTicketRepository,
    ImpersonationLogRepository,
    MaintenanceWindowRepository,
    PlatformAnnouncementRepository,
    AdminActionLogRepository,
    AIBackgroundJobRepository,
)

# Backwards compatibility re-exports
try:
    from api.repositories.prompt import PromptRepository, CollectionRepository, FolderRepository
except ImportError:
    pass

try:
    from api.repositories.agent import AgentRepository
except ImportError:
    pass

try:
    from api.repositories.campaign import CampaignRepository
except ImportError:
    pass

try:
    from api.repositories.conversation import ConversationRepository
except ImportError:
    pass

__all__ = [
    # Exceptions & Framework
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "OptimisticLockError",
    "TenantViolationError",
    "DatabaseConstraintError",
    "OffsetParams",
    "CursorParams",
    "PageResult",
    "CursorResult",
    "FilterParam",
    "FilterOperator",
    "apply_filters",
    "SortParam",
    "SortDirection",
    "apply_sorting",
    "QueryOptions",
    "IBaseRepository",
    "ITenantRepository",
    "IAuditRepository",
    "ISearchRepository",
    "BaseRepository",
    "TenantRepository",
    "AuditRepository",
    "SearchRepository",
    "UnitOfWork",
    # Sprint 1 Core Platform
    "OrganizationRepository",
    "UserRepository",
    "UserOrganizationRepository",
    "SystemConfigRepository",
    "AuditLogRepository",
    # Sprint 2 IAM
    "UserSessionRepository",
    "APIKeyRepository",
    "PasswordResetTokenRepository",
    "OAuthAccountRepository",
    "OrganizationInvitationRepository",
    # Sprint 3 AI Gateway
    "AIProviderRepository",
    "AIModelRepository",
    "AIRequestRepository",
    "AITokenUsageRepository",
    "AIRoutingPolicyRepository",
    # Sprint 4 Prompt Platform
    "EnterprisePromptRepository",
    "EnterprisePromptCollectionRepository",
    "EnterprisePromptFolderRepository",
    "PromptTestCaseRepository",
    "PromptEvaluationRepository",
    "PromptABTestRepository",
    # Sprint 5 Knowledge Platform
    "KnowledgeDocumentRepository",
    "DocumentChunkRepository",
    "KnowledgeCollectionRepository",
    "KnowledgeFolderRepository",
    "KnowledgeProcessingJobRepository",
    "FileAssetRepository",
    # Sprint 6 AI Agents
    "EnterpriseAgentDefinitionRepository",
    "AgentSessionRepository",
    "AgentRunRepository",
    "AgentToolRepository",
    "AgentMemoryRepository",
    # Sprint 7 Workflow Engine
    "WorkflowDefinitionRepository",
    "WorkflowExecutionRepository",
    "WorkflowStepRepository",
    "WorkflowTriggerRepository",
    # Sprint 8 Marketing Platform
    "EnterpriseCampaignRepository",
    "CampaignTemplateRepository",
    "CampaignAudienceRepository",
    "GeneratedContentRepository",
    # Sprint 9 CRM
    "CompanyRepository",
    "ContactRepository",
    "LeadRepository",
    "ActivityRepository",
    "DealRepository",
    # Sprint 10 Integrations
    "IntegrationRepository",
    "IntegrationCredentialRepository",
    "SyncJobRepository",
    "WebhookEndpointRepository",
    "WebhookDeliveryRepository",
    # Sprint 11 Notifications
    "NotificationRepository",
    "NotificationPreferenceRepository",
    "NotificationTemplateRepository",
    # Sprint 12 Billing
    "BillingPlanRepository",
    "SubscriptionRepository",
    "InvoiceRepository",
    "PaymentRepository",
    "CreditRepository",
    "UsageRecordRepository",
    # Sprint 13 Analytics
    "AnalyticsDashboardRepository",
    "AnalyticsWidgetRepository",
    "AnalyticsReportRepository",
    "AnalyticsEventRepository",
    "AnalyticsSnapshotRepository",
    # Sprint 14 Security
    "SecurityIncidentRepository",
    "ThreatDetectionRepository",
    "ComplianceAssessmentRepository",
    "PiiScanResultRepository",
    "SecurityEventLogRepository",
    # Sprint 15 Administration
    "SupportTicketRepository",
    "ImpersonationLogRepository",
    "MaintenanceWindowRepository",
    "PlatformAnnouncementRepository",
    "AdminActionLogRepository",
    "AIBackgroundJobRepository",
]
