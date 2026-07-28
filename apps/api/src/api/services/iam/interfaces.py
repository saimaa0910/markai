"""
EAIMOS IAM Service Interfaces
================================
Protocol-based structural interfaces for all Sprint 2 IAM services.
Enables strict typing, IDE intellisense, and allows alternative implementations
(mocks, test doubles, adapters) without inheriting from concrete classes.
"""

from __future__ import annotations

from typing import List, Optional, Protocol, Union
import uuid

from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.iam.dtos import (
    APIKeyCreatedDTO,
    APIKeyListDTO,
    APIKeyResponseDTO,
    AcceptInvitationDTO,
    ConsumePasswordResetDTO,
    CreateAPIKeyDTO,
    CreatePermissionDTO,
    CreateRoleDTO,
    CreateSessionDTO,
    AssignPermissionToRoleDTO,
    AssignRoleDTO,
    EffectivePermissionsDTO,
    InvitationListDTO,
    InvitationResponseDTO,
    IPCheckResultDTO,
    LinkOAuthAccountDTO,
    OAuthAccountResponseDTO,
    PasswordResetResponseDTO,
    PasswordValidationResultDTO,
    RefreshTokenResponseDTO,
    RequestPasswordResetDTO,
    RevokeRoleDTO,
    RevokeSessionDTO,
    RoleListDTO,
    RoleResponseDTO,
    RotateTokenDTO,
    SecurityPolicyResponseDTO,
    SendInvitationDTO,
    SessionListDTO,
    SessionResponseDTO,
    UpdateAPIKeyDTO,
    UpdateRoleDTO,
    UpdateSecurityPolicyDTO,
)


# =============================================================================
# ISessionService
# =============================================================================

class ISessionService(Protocol):
    """Interface for authenticated user session lifecycle management."""

    async def create_session(
        self,
        ctx: ServiceContext,
        dto: CreateSessionDTO,
    ) -> ServiceResult[SessionResponseDTO]: ...

    async def get_session(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SessionResponseDTO]: ...

    async def list_user_sessions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        include_revoked: bool = False,
    ) -> ServiceResult[SessionListDTO]: ...

    async def revoke_session(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
        dto: RevokeSessionDTO,
    ) -> ServiceResult[bool]: ...

    async def revoke_all_user_sessions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        reason: str,
    ) -> ServiceResult[int]: ...

    async def refresh_session_activity(
        self,
        ctx: ServiceContext,
        session_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]: ...


# =============================================================================
# IAPIKeyService
# =============================================================================

class IAPIKeyService(Protocol):
    """Interface for API key lifecycle and authentication."""

    async def create_api_key(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateAPIKeyDTO,
    ) -> ServiceResult[APIKeyCreatedDTO]: ...

    async def get_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
    ) -> ServiceResult[APIKeyResponseDTO]: ...

    async def list_api_keys(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        page: int = 1,
        page_size: int = 20,
    ) -> ServiceResult[APIKeyListDTO]: ...

    async def update_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
        dto: UpdateAPIKeyDTO,
    ) -> ServiceResult[APIKeyResponseDTO]: ...

    async def revoke_api_key(
        self,
        ctx: ServiceContext,
        api_key_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]: ...

    async def validate_api_key(
        self,
        raw_key: str,
        ip_address: Optional[str] = None,
    ) -> ServiceResult[APIKeyResponseDTO]: ...

    async def record_api_key_usage(
        self,
        api_key_id: Union[uuid.UUID, str],
        ip_address: Optional[str] = None,
    ) -> ServiceResult[bool]: ...


# =============================================================================
# IRoleService
# =============================================================================

class IRoleService(Protocol):
    """Interface for RBAC role and permission management."""

    async def create_role(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]: ...

    async def get_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
    ) -> ServiceResult[RoleResponseDTO]: ...

    async def list_roles(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        include_system: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> ServiceResult[RoleListDTO]: ...

    async def update_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        dto: UpdateRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]: ...

    async def delete_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]: ...

    async def assign_permission(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        dto: AssignPermissionToRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]: ...

    async def remove_permission(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        permission_id: Union[uuid.UUID, str],
    ) -> ServiceResult[RoleResponseDTO]: ...

    async def assign_role_to_user(
        self,
        ctx: ServiceContext,
        dto: AssignRoleDTO,
    ) -> ServiceResult[bool]: ...

    async def revoke_role_from_user(
        self,
        ctx: ServiceContext,
        dto: RevokeRoleDTO,
    ) -> ServiceResult[bool]: ...

    async def get_effective_permissions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[EffectivePermissionsDTO]: ...


# =============================================================================
# IInvitationService
# =============================================================================

class IInvitationService(Protocol):
    """Interface for organization invitation lifecycle."""

    async def send_invitation(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: SendInvitationDTO,
    ) -> ServiceResult[InvitationResponseDTO]: ...

    async def accept_invitation(
        self,
        ctx: ServiceContext,
        dto: AcceptInvitationDTO,
    ) -> ServiceResult[InvitationResponseDTO]: ...

    async def reject_invitation(
        self,
        ctx: ServiceContext,
        token: str,
    ) -> ServiceResult[bool]: ...

    async def cancel_invitation(
        self,
        ctx: ServiceContext,
        invitation_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]: ...

    async def resend_invitation(
        self,
        ctx: ServiceContext,
        invitation_id: Union[uuid.UUID, str],
    ) -> ServiceResult[InvitationResponseDTO]: ...

    async def get_invitation_by_token(
        self,
        ctx: ServiceContext,
        token: str,
    ) -> ServiceResult[InvitationResponseDTO]: ...

    async def list_invitations(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ServiceResult[InvitationListDTO]: ...


# =============================================================================
# ISecurityPolicyService
# =============================================================================

class ISecurityPolicyService(Protocol):
    """Interface for organization security policy management."""

    async def get_security_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SecurityPolicyResponseDTO]: ...

    async def update_security_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: UpdateSecurityPolicyDTO,
    ) -> ServiceResult[SecurityPolicyResponseDTO]: ...

    async def create_default_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SecurityPolicyResponseDTO]: ...

    async def validate_password_against_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        password_plaintext: str,
    ) -> ServiceResult[PasswordValidationResultDTO]: ...

    async def check_ip_allowed(
        self,
        org_id: Union[uuid.UUID, str],
        ip_address: str,
    ) -> ServiceResult[IPCheckResultDTO]: ...


# =============================================================================
# IOAuthService
# =============================================================================

class IOAuthService(Protocol):
    """Interface for OAuth provider account linking and SSO provisioning."""

    async def link_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        dto: LinkOAuthAccountDTO,
    ) -> ServiceResult[OAuthAccountResponseDTO]: ...

    async def unlink_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        provider: str,
    ) -> ServiceResult[bool]: ...

    async def get_oauth_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        provider: str,
    ) -> ServiceResult[OAuthAccountResponseDTO]: ...

    async def list_user_oauth_accounts(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[List[OAuthAccountResponseDTO]]: ...

    async def get_or_create_user_from_oauth(
        self,
        ctx: ServiceContext,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str],
        full_name: Optional[str],
        access_token_encrypted: Optional[str] = None,
        refresh_token_encrypted: Optional[str] = None,
    ) -> ServiceResult[dict]: ...
