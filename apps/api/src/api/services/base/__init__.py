"""
EAIMOS Enterprise Base Service Infrastructure (Sprint 0)
======================================================
Comprehensive Service Layer foundation providing Clean Architecture, DDD, UnitOfWork,
ServiceContext, ServiceResult, Exception Hierarchy, Authorization, Caching, Domain Events,
Event Dispatcher, Dependency Injection, and BaseService orchestrations.
"""

from api.services.base.authorization import AuthorizationService
from api.services.base.base_service import BaseService
from api.services.base.cache import ICacheManager, InMemoryCacheManager, RedisCacheManager
from api.services.base.dependency_provider import ServiceContainer, container
from api.services.base.event_dispatcher import EventDispatcher
from api.services.base.events import (
    AIRequestCompleted,
    CampaignLaunched,
    DomainEvent,
    EntityCreated,
    EntityDeleted,
    EntityRestored,
    EntityUpdated,
    InvoicePaid,
    KnowledgeIndexed,
    NotificationSent,
    PromptPublished,
    WorkflowCompleted,
    WorkflowStarted,
)
from api.services.base.interfaces import IAuthorizer, IBaseService, IEventDispatcherProtocol
from api.services.base.permissions import DEFAULT_ROLE_PERMISSIONS, EnterprisePermission
from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import (
    AlreadyExistsError,
    BusinessRuleViolation,
    ConflictError,
    ExternalServiceError,
    ForbiddenOperation,
    NotFoundError,
    ServiceError,
    UnauthorizedOperation,
    ValidationError,
)
from api.services.base.service_result import ServiceResult
from api.services.base.unit_of_work_service import UnitOfWorkService, transactional
from api.services.base.validators import (
    ValidatorChain,
    validate_business_rule,
    validate_cross_fields,
    validate_required,
)

__all__ = [
    # Base Service & Context & Result
    "BaseService",
    "ServiceContext",
    "ServiceResult",
    # Exception Hierarchy
    "ServiceError",
    "ValidationError",
    "BusinessRuleViolation",
    "UnauthorizedOperation",
    "ForbiddenOperation",
    "ConflictError",
    "AlreadyExistsError",
    "NotFoundError",
    "ExternalServiceError",
    # Permissions & Authorization
    "EnterprisePermission",
    "DEFAULT_ROLE_PERMISSIONS",
    "AuthorizationService",
    # Caching
    "ICacheManager",
    "InMemoryCacheManager",
    "RedisCacheManager",
    # Domain Events & Dispatcher
    "DomainEvent",
    "EntityCreated",
    "EntityUpdated",
    "EntityDeleted",
    "EntityRestored",
    "WorkflowStarted",
    "WorkflowCompleted",
    "AIRequestCompleted",
    "PromptPublished",
    "KnowledgeIndexed",
    "CampaignLaunched",
    "InvoicePaid",
    "NotificationSent",
    "EventDispatcher",
    # Transaction & UoW
    "UnitOfWorkService",
    "transactional",
    # Dependency Injection
    "ServiceContainer",
    "container",
    # Validation
    "ValidatorChain",
    "validate_required",
    "validate_business_rule",
    "validate_cross_fields",
    # Interfaces
    "IBaseService",
    "IAuthorizer",
    "IEventDispatcherProtocol",
]
