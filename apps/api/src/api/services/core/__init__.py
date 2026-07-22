"""
EAIMOS Core Platform Services Package (Sprint 1)
================================================
Provides domain services for Organization Management, User Identity Management,
Organization Memberships & Seat Quotas, System Configuration Parameters, and Audit Logging.
"""

from api.services.core.audit_log_service import AuditLogService, CreateAuditLogDTO
from api.services.core.membership_service import (
    CreateMembershipDTO,
    UpdateMembershipDTO,
    UserOrganizationService,
)
from api.services.core.organization_service import (
    CreateOrganizationDTO,
    OrganizationService,
    UpdateOrganizationDTO,
)
from api.services.core.system_config_service import (
    CreateConfigDTO,
    SystemConfigService,
    UpdateConfigDTO,
)
from api.services.core.user_service import CreateUserDTO, UpdateUserDTO, UserService

__all__ = [
    # Organization Service
    "OrganizationService",
    "CreateOrganizationDTO",
    "UpdateOrganizationDTO",
    # User Service
    "UserService",
    "CreateUserDTO",
    "UpdateUserDTO",
    # Membership Service
    "UserOrganizationService",
    "CreateMembershipDTO",
    "UpdateMembershipDTO",
    # System Config Service
    "SystemConfigService",
    "CreateConfigDTO",
    "UpdateConfigDTO",
    # Audit Log Service
    "AuditLogService",
    "CreateAuditLogDTO",
]
