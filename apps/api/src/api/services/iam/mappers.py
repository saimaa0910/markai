"""
EAIMOS IAM Mapper Utilities
=============================
Converts ORM entity objects to Pydantic response DTOs for the IAM service layer.
Keeps mapping logic in one place, preventing DTO construction from leaking into services.
All mappers are pure functions — no I/O, no side effects.
"""

from __future__ import annotations

from typing import Any, List, Optional

from api.services.iam.dtos import (
    APIKeyResponseDTO,
    APIKeySummaryDTO,
    EffectivePermissionsDTO,
    InvitationResponseDTO,
    InvitationSummaryDTO,
    OAuthAccountResponseDTO,
    PasswordResetResponseDTO,
    PermissionResponseDTO,
    RefreshTokenResponseDTO,
    RoleResponseDTO,
    RoleSummaryDTO,
    SecurityPolicyResponseDTO,
    SessionResponseDTO,
    SessionSummaryDTO,
    UserRoleResponseDTO,
)


# =============================================================================
# Session Mappers
# =============================================================================

def session_to_response_dto(entity: Any) -> SessionResponseDTO:
    """Map a UserSession ORM object to a full SessionResponseDTO."""
    return SessionResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        organization_id=getattr(entity, "organization_id", None),
        ip_address=getattr(entity, "ip_address", None),
        user_agent=getattr(entity, "user_agent", None),
        country_code=getattr(entity, "country_code", None),
        city=getattr(entity, "city", None),
        expires_at=entity.expires_at,
        last_active_at=entity.last_active_at,
        is_revoked=entity.is_revoked,
        revoked_at=getattr(entity, "revoked_at", None),
        revocation_reason=getattr(entity, "revocation_reason", None),
        created_at=entity.created_at,
    )


def session_to_summary_dto(entity: Any) -> SessionSummaryDTO:
    """Map a UserSession ORM object to a compact SessionSummaryDTO."""
    return SessionSummaryDTO(
        id=entity.id,
        user_id=entity.user_id,
        ip_address=getattr(entity, "ip_address", None),
        country_code=getattr(entity, "country_code", None),
        city=getattr(entity, "city", None),
        last_active_at=entity.last_active_at,
        expires_at=entity.expires_at,
        is_revoked=entity.is_revoked,
    )


def sessions_to_summary_list(entities: List[Any]) -> List[SessionSummaryDTO]:
    """Batch-map a list of UserSession entities to summary DTOs."""
    return [session_to_summary_dto(e) for e in entities]


# =============================================================================
# Refresh Token Mappers
# =============================================================================

def refresh_token_to_response_dto(entity: Any) -> RefreshTokenResponseDTO:
    """Map a RefreshToken ORM object to a RefreshTokenResponseDTO."""
    return RefreshTokenResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        session_id=entity.session_id,
        family_id=entity.family_id,
        expires_at=entity.expires_at,
        is_used=entity.is_used,
        is_revoked=entity.is_revoked,
    )


# =============================================================================
# Password Reset Mappers
# =============================================================================

def password_reset_to_response_dto(entity: Any) -> PasswordResetResponseDTO:
    """Map a PasswordResetToken ORM object to a PasswordResetResponseDTO."""
    return PasswordResetResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        expires_at=entity.expires_at,
        is_used=entity.is_used,
    )


# =============================================================================
# API Key Mappers
# =============================================================================

def api_key_to_response_dto(entity: Any) -> APIKeyResponseDTO:
    """
    Map an APIKey ORM object to a full APIKeyResponseDTO.
    NEVER includes key_hash or any raw key material.
    """
    return APIKeyResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        user_id=entity.user_id,
        name=entity.name,
        key_prefix=entity.key_prefix,
        scopes=list(entity.scopes or []),
        allowed_ips=list(entity.allowed_ips) if entity.allowed_ips else None,
        expires_at=getattr(entity, "expires_at", None),
        is_active=entity.is_active,
        rate_limit_rpm=entity.rate_limit_rpm,
        last_used_at=getattr(entity, "last_used_at", None),
        total_calls=entity.total_calls,
        created_at=entity.created_at,
        updated_at=getattr(entity, "updated_at", None),
    )


def api_key_to_summary_dto(entity: Any) -> APIKeySummaryDTO:
    """Map an APIKey ORM object to a compact APIKeySummaryDTO for list views."""
    return APIKeySummaryDTO(
        id=entity.id,
        name=entity.name,
        key_prefix=entity.key_prefix,
        scopes=list(entity.scopes or []),
        is_active=entity.is_active,
        expires_at=getattr(entity, "expires_at", None),
        last_used_at=getattr(entity, "last_used_at", None),
        total_calls=entity.total_calls,
    )


def api_keys_to_summary_list(entities: List[Any]) -> List[APIKeySummaryDTO]:
    """Batch-map API key entities to summary DTOs."""
    return [api_key_to_summary_dto(e) for e in entities]


# =============================================================================
# Role & Permission Mappers
# =============================================================================

def permission_to_response_dto(entity: Any) -> PermissionResponseDTO:
    """Map a Permission ORM object to a PermissionResponseDTO."""
    return PermissionResponseDTO(
        id=entity.id,
        resource=entity.resource,
        action=entity.action,
        scope=entity.scope,
        description=getattr(entity, "description", None),
        created_at=entity.created_at,
    )


def permissions_to_response_list(entities: List[Any]) -> List[PermissionResponseDTO]:
    """Batch-map permission entities to response DTOs."""
    return [permission_to_response_dto(e) for e in entities]


def role_to_response_dto(entity: Any, include_permissions: bool = True) -> RoleResponseDTO:
    """
    Map a Role ORM object to a full RoleResponseDTO.
    Optionally includes nested permission list.
    """
    perms: List[PermissionResponseDTO] = []
    if include_permissions and hasattr(entity, "permissions") and entity.permissions:
        perms = [permission_to_response_dto(p) for p in entity.permissions]

    return RoleResponseDTO(
        id=entity.id,
        organization_id=getattr(entity, "organization_id", None),
        name=entity.name,
        display_name=getattr(entity, "display_name", None),
        description=getattr(entity, "description", None),
        is_system=entity.is_system,
        is_default=entity.is_default,
        permissions=perms,
        created_at=entity.created_at,
        updated_at=getattr(entity, "updated_at", None),
    )


def role_to_summary_dto(entity: Any) -> RoleSummaryDTO:
    """Map a Role ORM object to a compact RoleSummaryDTO."""
    perm_count = 0
    if hasattr(entity, "permissions") and entity.permissions:
        perm_count = len(entity.permissions)
    return RoleSummaryDTO(
        id=entity.id,
        name=entity.name,
        display_name=getattr(entity, "display_name", None),
        is_system=entity.is_system,
        is_default=entity.is_default,
        permission_count=perm_count,
    )


def roles_to_summary_list(entities: List[Any]) -> List[RoleSummaryDTO]:
    """Batch-map role entities to summary DTOs."""
    return [role_to_summary_dto(e) for e in entities]


def user_role_to_response_dto(entity: Any) -> UserRoleResponseDTO:
    """Map a UserRole ORM assignment to a UserRoleResponseDTO."""
    role_summary: Optional[RoleSummaryDTO] = None
    if hasattr(entity, "role") and entity.role:
        role_summary = role_to_summary_dto(entity.role)

    return UserRoleResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        role_id=entity.role_id,
        organization_id=entity.organization_id,
        granted_by=getattr(entity, "granted_by", None),
        expires_at=getattr(entity, "expires_at", None),
        role=role_summary,
    )


def build_effective_permissions_dto(
    user_id: str,
    org_id: str,
    role_assignments: List[Any],
    is_super_admin: bool = False,
) -> EffectivePermissionsDTO:
    """
    Resolve the full effective permission set for a user in an org by
    iterating their role assignments and collecting unique permissions.
    """
    role_names: List[str] = []
    permission_labels: List[str] = []

    for assignment in role_assignments:
        if hasattr(assignment, "role") and assignment.role:
            role = assignment.role
            role_names.append(role.name)
            if hasattr(role, "permissions") and role.permissions:
                for perm in role.permissions:
                    label = f"{perm.resource}:{perm.action}:{perm.scope}"
                    if label not in permission_labels:
                        permission_labels.append(label)

    return EffectivePermissionsDTO(
        user_id=user_id,  # type: ignore[arg-type]
        organization_id=org_id,  # type: ignore[arg-type]
        roles=role_names,
        permissions=permission_labels,
        is_super_admin=is_super_admin,
    )


# =============================================================================
# Invitation Mappers
# =============================================================================

def invitation_to_response_dto(entity: Any) -> InvitationResponseDTO:
    """Map an OrganizationInvitation ORM object to a full InvitationResponseDTO."""
    return InvitationResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        invited_by=getattr(entity, "invited_by", None),
        email=entity.email,
        role=entity.role.value if hasattr(entity.role, "value") else str(entity.role),
        message=getattr(entity, "message", None),
        token=entity.token,
        is_accepted=entity.is_accepted,
        is_rejected=entity.is_rejected,
        accepted_at=getattr(entity, "accepted_at", None),
        expires_at=entity.expires_at,
        created_at=entity.created_at,
    )


def invitation_to_summary_dto(entity: Any) -> InvitationSummaryDTO:
    """Map an invitation to a compact summary (token hidden)."""
    return InvitationSummaryDTO(
        id=entity.id,
        email=entity.email,
        role=entity.role.value if hasattr(entity.role, "value") else str(entity.role),
        is_accepted=entity.is_accepted,
        is_rejected=entity.is_rejected,
        expires_at=entity.expires_at,
        created_at=entity.created_at,
    )


def invitations_to_summary_list(entities: List[Any]) -> List[InvitationSummaryDTO]:
    """Batch-map invitation entities to summary DTOs."""
    return [invitation_to_summary_dto(e) for e in entities]


# =============================================================================
# Security Policy Mappers
# =============================================================================

def security_policy_to_response_dto(entity: Any) -> SecurityPolicyResponseDTO:
    """Map a SecurityPolicy ORM object to a SecurityPolicyResponseDTO."""
    return SecurityPolicyResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        mfa_required=entity.mfa_required,
        allowed_mfa_methods=list(entity.allowed_mfa_methods) if entity.allowed_mfa_methods else None,
        password_min_length=entity.password_min_length,
        password_require_uppercase=entity.password_require_uppercase,
        password_require_numbers=entity.password_require_numbers,
        password_require_symbols=entity.password_require_symbols,
        password_history_count=entity.password_history_count,
        session_timeout_minutes=entity.session_timeout_minutes,
        max_concurrent_sessions=entity.max_concurrent_sessions,
        max_failed_logins=entity.max_failed_logins,
        lockout_duration_minutes=entity.lockout_duration_minutes,
        allowed_ip_ranges=list(entity.allowed_ip_ranges) if entity.allowed_ip_ranges else None,
        sso_enforced=entity.sso_enforced,
        api_key_max_expiry_days=getattr(entity, "api_key_max_expiry_days", None),
        api_key_require_ip_restriction=entity.api_key_require_ip_restriction,
        created_at=entity.created_at,
        updated_at=getattr(entity, "updated_at", None),
    )


# =============================================================================
# OAuth Account Mappers
# =============================================================================

def oauth_account_to_response_dto(entity: Any) -> OAuthAccountResponseDTO:
    """
    Map an OAuthAccount ORM object to an OAuthAccountResponseDTO.
    NEVER includes encrypted token values.
    """
    return OAuthAccountResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        provider=entity.provider,
        provider_user_id=entity.provider_user_id,
        provider_email=getattr(entity, "provider_email", None),
        token_expires_at=getattr(entity, "token_expires_at", None),
        created_at=entity.created_at,
        updated_at=getattr(entity, "updated_at", None),
    )


def oauth_accounts_to_response_list(entities: List[Any]) -> List[OAuthAccountResponseDTO]:
    """Batch-map OAuth account entities to response DTOs."""
    return [oauth_account_to_response_dto(e) for e in entities]
