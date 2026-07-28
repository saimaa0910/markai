"""
EAIMOS IAM Service Layer (Sprint 2)
=====================================
Public API for the Identity & Access Management domain service module.
Exports all services, DTOs, events, validators, policies, mappers,
interfaces, cache keys, constants, and dependency providers.
"""

# ─── Services ─────────────────────────────────────────────────────────────────
from api.services.iam.session_service import SessionService
from api.services.iam.api_key_service import APIKeyService
from api.services.iam.role_service import RoleService
from api.services.iam.invitation_service import InvitationService
from api.services.iam.security_policy_service import SecurityPolicyService
from api.services.iam.oauth_service import OAuthService

# ─── DTOs ─────────────────────────────────────────────────────────────────────
from api.services.iam.dtos import (
    # Session
    CreateSessionDTO,
    SessionResponseDTO,
    SessionSummaryDTO,
    SessionListDTO,
    RevokeSessionDTO,
    # Refresh Token
    CreateRefreshTokenDTO,
    RefreshTokenResponseDTO,
    RotateTokenDTO,
    # Password Reset
    RequestPasswordResetDTO,
    ConsumePasswordResetDTO,
    PasswordResetResponseDTO,
    # API Key
    CreateAPIKeyDTO,
    UpdateAPIKeyDTO,
    APIKeyCreatedDTO,
    APIKeyResponseDTO,
    APIKeySummaryDTO,
    APIKeyListDTO,
    APIKeyFilterDTO,
    # Role
    CreateRoleDTO,
    UpdateRoleDTO,
    RoleResponseDTO,
    RoleSummaryDTO,
    RoleListDTO,
    # Permission
    CreatePermissionDTO,
    PermissionResponseDTO,
    AssignPermissionToRoleDTO,
    # User Role Assignment
    AssignRoleDTO,
    RevokeRoleDTO,
    UserRoleResponseDTO,
    EffectivePermissionsDTO,
    # Invitation
    SendInvitationDTO,
    AcceptInvitationDTO,
    InvitationResponseDTO,
    InvitationSummaryDTO,
    InvitationListDTO,
    InvitationFilterDTO,
    # Security Policy
    UpdateSecurityPolicyDTO,
    SecurityPolicyResponseDTO,
    PasswordValidationResultDTO,
    IPCheckResultDTO,
    # OAuth
    LinkOAuthAccountDTO,
    OAuthAccountResponseDTO,
    OAuthCallbackDTO,
    OAuthUserInfoDTO,
)

# ─── Events ───────────────────────────────────────────────────────────────────
from api.services.iam.events import (
    UserLoggedIn,
    UserLoggedOut,
    SessionRevoked,
    AllSessionsRevoked,
    RefreshTokenIssued,
    RefreshTokenRotated,
    RefreshTokenFamilyCompromised,
    PasswordResetRequested,
    PasswordResetConsumed,
    APIKeyCreated,
    APIKeyUpdated,
    APIKeyRevoked,
    APIKeyRotated,
    APIKeyUsed,
    RoleCreated,
    RoleUpdated,
    RoleDeleted,
    PermissionAssignedToRole,
    PermissionRemovedFromRole,
    RoleAssigned,
    RoleRevoked,
    InvitationSent,
    InvitationAccepted,
    InvitationRejected,
    InvitationCancelled,
    InvitationResent,
    InvitationExpired,
    SecurityPolicyCreated,
    SecurityPolicyUpdated,
    SecurityPolicyMFAEnabled,
    SecurityPolicyMFADisabled,
    SecurityPolicyIPRestrictionChanged,
    SecurityPolicySSOEnforced,
    OAuthAccountLinked,
    OAuthAccountUnlinked,
    OAuthTokenRefreshed,
    OAuthUserProvisioned,
)

# ─── Policies ─────────────────────────────────────────────────────────────────
from api.services.iam.policies import (
    SessionPolicy,
    APIKeyPolicy,
    RolePolicy,
    InvitationPolicy,
    SecurityPolicyPolicy,
    OAuthPolicy,
)

# ─── Validators ───────────────────────────────────────────────────────────────
from api.services.iam.validators import (
    validate_session_not_expired,
    validate_session_not_revoked,
    validate_max_concurrent_sessions,
    validate_token_not_expired,
    validate_token_not_used,
    validate_token_not_revoked,
    validate_refresh_token_family_not_compromised,
    validate_api_key_scopes,
    validate_api_key_ip_allowlist,
    validate_api_key_not_expired,
    validate_api_key_active,
    validate_api_key_limit_not_exceeded,
    validate_role_not_system,
    validate_role_name_format,
    validate_role_not_assigned_to_users,
    validate_user_role_not_duplicate,
    validate_role_not_expired,
    validate_invitation_not_expired,
    validate_invitation_not_accepted,
    validate_invitation_not_rejected,
    validate_no_pending_invitation,
    validate_password_against_policy,
    validate_ip_within_policy_ranges,
    validate_security_policy_not_looser_than_platform,
    validate_oauth_provider_supported,
    validate_oauth_account_not_already_linked,
    validate_oauth_provider_user_not_taken,
)

# ─── Mappers ──────────────────────────────────────────────────────────────────
from api.services.iam.mappers import (
    session_to_response_dto,
    session_to_summary_dto,
    sessions_to_summary_list,
    api_key_to_response_dto,
    api_key_to_summary_dto,
    api_keys_to_summary_list,
    permission_to_response_dto,
    role_to_response_dto,
    role_to_summary_dto,
    roles_to_summary_list,
    user_role_to_response_dto,
    build_effective_permissions_dto,
    invitation_to_response_dto,
    invitation_to_summary_dto,
    invitations_to_summary_list,
    security_policy_to_response_dto,
    oauth_account_to_response_dto,
    oauth_accounts_to_response_list,
)

# ─── Interfaces ───────────────────────────────────────────────────────────────
from api.services.iam.interfaces import (
    ISessionService,
    IAPIKeyService,
    IRoleService,
    IInvitationService,
    ISecurityPolicyService,
    IOAuthService,
)

# ─── Cache Keys ───────────────────────────────────────────────────────────────
from api.services.iam.cache_keys import (
    session_cache_key,
    user_sessions_list_key,
    api_key_by_id_cache_key,
    api_key_by_hash_cache_key,
    api_key_list_key,
    role_cache_key,
    org_roles_list_key,
    user_roles_cache_key,
    user_permissions_cache_key,
    invitation_by_token_cache_key,
    invitation_by_id_cache_key,
    org_invitations_list_key,
    security_policy_cache_key,
    oauth_account_cache_key,
    user_oauth_accounts_list_key,
)

# ─── Constants ────────────────────────────────────────────────────────────────
from api.services.iam.constants import (
    SESSION_TTL_MINUTES,
    REFRESH_TOKEN_TTL_DAYS,
    PASSWORD_RESET_TTL_MINUTES,
    API_KEY_MAX_PER_ORG,
    INVITE_EXPIRY_HOURS,
    SUPPORTED_OAUTH_PROVIDERS,
    SYSTEM_ROLE_NAMES,
    SECURITY_POLICY_DEFAULTS,
)

# ─── Dependencies ─────────────────────────────────────────────────────────────
from api.services.iam.dependencies import (
    get_session_service,
    get_api_key_service,
    get_role_service,
    get_invitation_service,
    get_security_policy_service,
    get_oauth_service,
)


__all__ = [
    # Services
    "SessionService",
    "APIKeyService",
    "RoleService",
    "InvitationService",
    "SecurityPolicyService",
    "OAuthService",
    # Interfaces
    "ISessionService",
    "IAPIKeyService",
    "IRoleService",
    "IInvitationService",
    "ISecurityPolicyService",
    "IOAuthService",
    # Session DTOs
    "CreateSessionDTO",
    "SessionResponseDTO",
    "SessionSummaryDTO",
    "SessionListDTO",
    "RevokeSessionDTO",
    # API Key DTOs
    "CreateAPIKeyDTO",
    "UpdateAPIKeyDTO",
    "APIKeyCreatedDTO",
    "APIKeyResponseDTO",
    "APIKeySummaryDTO",
    "APIKeyListDTO",
    # Role DTOs
    "CreateRoleDTO",
    "UpdateRoleDTO",
    "RoleResponseDTO",
    "RoleSummaryDTO",
    "RoleListDTO",
    "AssignPermissionToRoleDTO",
    "AssignRoleDTO",
    "RevokeRoleDTO",
    "EffectivePermissionsDTO",
    # Permission DTOs
    "CreatePermissionDTO",
    "PermissionResponseDTO",
    # Invitation DTOs
    "SendInvitationDTO",
    "AcceptInvitationDTO",
    "InvitationResponseDTO",
    "InvitationListDTO",
    # Security Policy DTOs
    "UpdateSecurityPolicyDTO",
    "SecurityPolicyResponseDTO",
    "PasswordValidationResultDTO",
    "IPCheckResultDTO",
    # OAuth DTOs
    "LinkOAuthAccountDTO",
    "OAuthAccountResponseDTO",
    "OAuthCallbackDTO",
    # Policies
    "SessionPolicy",
    "APIKeyPolicy",
    "RolePolicy",
    "InvitationPolicy",
    "SecurityPolicyPolicy",
    "OAuthPolicy",
    # Key events
    "UserLoggedIn",
    "UserLoggedOut",
    "APIKeyCreated",
    "APIKeyRevoked",
    "RoleCreated",
    "RoleAssigned",
    "InvitationSent",
    "InvitationAccepted",
    "SecurityPolicyUpdated",
    "OAuthAccountLinked",
    # Dependencies
    "get_session_service",
    "get_api_key_service",
    "get_role_service",
    "get_invitation_service",
    "get_security_policy_service",
    "get_oauth_service",
    # Constants
    "SESSION_TTL_MINUTES",
    "INVITE_EXPIRY_HOURS",
    "SUPPORTED_OAUTH_PROVIDERS",
    "SECURITY_POLICY_DEFAULTS",
]
