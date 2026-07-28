"""
Sprint 2 IAM Service Tests — CRUD Lifecycle
=============================================
Full lifecycle tests for all 6 IAM domain services:
SessionService, APIKeyService, RoleService, InvitationService,
SecurityPolicyService, OAuthService.
Uses in-memory repositories and cache for full isolation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.iam.api_key_service import APIKeyService
from api.services.iam.invitation_service import InvitationService
from api.services.iam.oauth_service import OAuthService
from api.services.iam.role_service import RoleService
from api.services.iam.security_policy_service import SecurityPolicyService
from api.services.iam.session_service import SessionService
from api.services.iam.dtos import (
    AcceptInvitationDTO,
    AssignPermissionToRoleDTO,
    AssignRoleDTO,
    CreateAPIKeyDTO,
    CreateRoleDTO,
    CreateSessionDTO,
    LinkOAuthAccountDTO,
    RevokeRoleDTO,
    RevokeSessionDTO,
    SendInvitationDTO,
    UpdateAPIKeyDTO,
    UpdateRoleDTO,
    UpdateSecurityPolicyDTO,
)


# =============================================================================
# Fixtures
# =============================================================================

def make_ctx(
    user_id: Optional[str] = None,
    org_id: Optional[str] = None,
    is_super: bool = False,
) -> ServiceContext:
    """Build a mock ServiceContext for testing."""
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.UUID(user_id) if user_id else uuid.uuid4()
    ctx.organization_id = uuid.UUID(org_id) if org_id else uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.is_super_admin = is_super
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer(
    allow_all: bool = True,
    deny_permission: Optional[str] = None,
) -> MagicMock:
    """Build a mock AuthorizationService."""
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = allow_all
    auth.check_ownership.return_value = True
    return auth


def make_uow(entities: Optional[dict] = None) -> MagicMock:
    """Build a mock UnitOfWorkService that stores created entities in memory."""
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()

    _store: dict = entities or {}
    _events = []

    def add_event(event):
        _events.append(event)

    uow.add_event.side_effect = add_event
    uow._events = _events

    return uow


def make_entity(**kwargs) -> MagicMock:
    """Build a mock ORM entity with standard fields."""
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    entity.updated_at = None
    entity.deleted_at = None
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


# =============================================================================
# SessionService Tests
# =============================================================================

class TestSessionService:
    """Tests for SessionService CRUD lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.user_id = self.ctx.user_id
        self.org_id = self.ctx.organization_id

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """SessionService.create_session() returns a valid session with a future expiry."""
        session_entity = make_entity(
            user_id=self.user_id,
            organization_id=self.org_id,
            ip_address="1.2.3.4",
            user_agent="pytest/1.0",
            device_fingerprint=None,
            country_code="US",
            city="New York",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            last_active_at=datetime.now(timezone.utc),
            is_revoked=False,
            revoked_at=None,
            revocation_reason=None,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.list_user_sessions.return_value = []
        repo_mock.create.return_value = session_entity
        uow.get_repository.return_value = repo_mock

        svc = SessionService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        dto = CreateSessionDTO(
            user_id=self.user_id,
            organization_id=self.org_id,
            ip_address="1.2.3.4",
            user_agent="pytest/1.0",
            country_code="US",
            city="New York",
        )

        result = await svc.create_session(self.ctx, dto)

        assert result.is_success
        assert result.status_code == 201
        assert result.data.user_id == self.user_id
        assert result.data.ip_address == "1.2.3.4"
        assert result.data.is_revoked is False
        assert len(uow._events) == 1
        assert uow._events[0].event_type == "iam.user.logged_in"

    @pytest.mark.asyncio
    async def test_get_session_cache_hit(self):
        """get_session() returns cached data without hitting the repository."""
        session_id = uuid.uuid4()
        session_data = {
            "id": str(session_id),
            "user_id": str(self.user_id),
            "organization_id": str(self.org_id),
            "ip_address": "1.2.3.4",
            "user_agent": None,
            "country_code": "US",
            "city": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "last_active_at": datetime.now(timezone.utc).isoformat(),
            "is_revoked": False,
            "revoked_at": None,
            "revocation_reason": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        from api.services.iam.cache_keys import session_cache_key
        await self.cache.set(session_cache_key(session_id), session_data)

        uow = make_uow()
        repo_mock = AsyncMock()
        uow.get_repository.return_value = repo_mock

        svc = SessionService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        result = await svc.get_session(self.ctx, session_id)

        assert result.is_success
        assert result.metadata.get("cached") is True
        # Repository should NOT be called
        repo_mock.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_revoke_session_success(self):
        """revoke_session() marks the session as revoked and publishes SessionRevoked event."""
        session_id = uuid.uuid4()
        session_entity = make_entity(
            id=session_id,
            user_id=self.user_id,
            organization_id=self.org_id,
            is_revoked=False,
            revoked_at=None,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = session_entity
        repo_mock.update.return_value = session_entity
        uow.get_repository.return_value = repo_mock

        svc = SessionService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        result = await svc.revoke_session(
            self.ctx,
            session_id,
            RevokeSessionDTO(reason="admin"),
        )

        assert result.is_success
        assert result.data is True
        assert any(e.event_type == "iam.session.revoked" for e in uow._events)

    @pytest.mark.asyncio
    async def test_revoke_all_user_sessions(self):
        """revoke_all_user_sessions() revokes every active session and returns count."""
        sessions = [
            make_entity(id=uuid.uuid4(), user_id=self.user_id, is_revoked=False),
            make_entity(id=uuid.uuid4(), user_id=self.user_id, is_revoked=False),
            make_entity(id=uuid.uuid4(), user_id=self.user_id, is_revoked=True),  # already revoked
        ]

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.list_user_sessions.return_value = sessions
        repo_mock.update.return_value = None
        uow.get_repository.return_value = repo_mock

        svc = SessionService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        result = await svc.revoke_all_user_sessions(
            self.ctx,
            user_id=self.user_id,
            reason="password_change",
        )

        assert result.is_success
        assert result.data == 2  # Only 2 active sessions revoked
        assert any(e.event_type == "iam.session.all_revoked" for e in uow._events)


# =============================================================================
# APIKeyService Tests
# =============================================================================

class TestAPIKeyService:
    """Tests for APIKeyService CRUD lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.org_id = self.ctx.organization_id

    @pytest.mark.asyncio
    async def test_create_api_key_returns_plaintext_once(self):
        """create_api_key() returns APIKeyCreatedDTO with raw_key on first creation."""
        key_entity = make_entity(
            organization_id=self.org_id,
            user_id=self.ctx.user_id,
            name="Test Key",
            key_prefix="mk_live_Test",
            key_hash="fakehash",
            scopes=["prompts:read"],
            allowed_ips=None,
            expires_at=None,
            is_active=True,
            rate_limit_rpm=60,
            total_calls=0,
            last_used_at=None,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_many.return_value = []
        repo_mock.create.return_value = key_entity
        uow.get_repository.return_value = repo_mock

        svc = APIKeyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.api_key_service.APIKeyRepository", return_value=repo_mock):
            result = await svc.create_api_key(
                self.ctx,
                org_id=self.org_id,
                dto=CreateAPIKeyDTO(name="Test Key", scopes=["prompts:read"]),
            )

        assert result.is_success
        assert result.status_code == 201
        assert result.data.raw_key.startswith("mk_live_")
        assert result.data.name == "Test Key"
        assert len(uow._events) == 1
        assert uow._events[0].event_type == "iam.api_key.created"

    @pytest.mark.asyncio
    async def test_revoke_api_key(self):
        """revoke_api_key() soft-deletes the key and publishes APIKeyRevoked event."""
        key_id = uuid.uuid4()
        key_entity = make_entity(
            id=key_id,
            organization_id=self.org_id,
            user_id=self.ctx.user_id,
            name="My Key",
            key_prefix="mk_live_My",
            is_active=True,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = key_entity
        repo_mock.soft_delete.return_value = None
        uow.get_repository.return_value = repo_mock

        svc = APIKeyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.api_key_service.APIKeyRepository", return_value=repo_mock):
            result = await svc.revoke_api_key(self.ctx, key_id)

        assert result.is_success
        assert result.data is True
        assert any(e.event_type == "iam.api_key.revoked" for e in uow._events)

    @pytest.mark.asyncio
    async def test_update_api_key(self):
        """update_api_key() updates name and scopes and invalidates cache."""
        key_id = uuid.uuid4()
        key_entity = make_entity(
            id=key_id,
            organization_id=self.org_id,
            user_id=self.ctx.user_id,
            name="Old Name",
            key_prefix="mk_live_Old",
            scopes=["prompts:read"],
            allowed_ips=None,
            expires_at=None,
            is_active=True,
            rate_limit_rpm=60,
            total_calls=0,
            last_used_at=None,
        )
        updated_entity = make_entity(
            id=key_id,
            organization_id=self.org_id,
            user_id=self.ctx.user_id,
            name="New Name",
            key_prefix="mk_live_Old",
            scopes=["prompts:read", "agents:read"],
            allowed_ips=None,
            expires_at=None,
            is_active=True,
            rate_limit_rpm=60,
            total_calls=0,
            last_used_at=None,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = key_entity
        repo_mock.update.return_value = updated_entity
        uow.get_repository.return_value = repo_mock

        svc = APIKeyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.api_key_service.APIKeyRepository", return_value=repo_mock):
            result = await svc.update_api_key(
                self.ctx,
                api_key_id=key_id,
                dto=UpdateAPIKeyDTO(name="New Name", scopes=["prompts:read", "agents:read"]),
            )

        assert result.is_success
        assert result.data.name == "New Name"
        assert any(e.event_type == "iam.api_key.updated" for e in uow._events)


# =============================================================================
# RoleService Tests
# =============================================================================

class TestRoleService:
    """Tests for RoleService CRUD lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.org_id = self.ctx.organization_id

    @pytest.mark.asyncio
    async def test_create_role_success(self):
        """create_role() creates a custom org role and publishes RoleCreated event."""
        role_entity = make_entity(
            organization_id=self.org_id,
            name="CONTENT_MANAGER",
            display_name="Content Manager",
            description=None,
            is_system=False,
            is_default=False,
            permissions=[],
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = None  # No duplicate
        repo_mock.create.return_value = role_entity
        uow.get_repository.return_value = repo_mock

        svc = RoleService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.role_service._RoleRepository", return_value=repo_mock):
            result = await svc.create_role(
                self.ctx,
                org_id=self.org_id,
                dto=CreateRoleDTO(name="CONTENT_MANAGER", display_name="Content Manager"),
            )

        assert result.is_success
        assert result.status_code == 201
        assert result.data.name == "CONTENT_MANAGER"
        assert result.data.is_system is False
        assert any(e.event_type == "iam.role.created" for e in uow._events)

    @pytest.mark.asyncio
    async def test_delete_system_role_forbidden(self):
        """delete_role() raises ForbiddenOperation when role.is_system=True."""
        from api.services.base.service_exceptions import ForbiddenOperation

        role_entity = make_entity(
            organization_id=self.org_id,
            name="ADMIN",
            is_system=True,
            is_default=True,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = role_entity
        uow.get_repository.return_value = repo_mock

        svc = RoleService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.role_service._RoleRepository", return_value=repo_mock):
            result = await svc.delete_role(self.ctx, role_id=uuid.uuid4())

        assert result.is_failure
        assert "system" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_assign_role_to_user(self):
        """assign_role_to_user() creates a UserRole record and publishes RoleAssigned event."""
        role_entity = make_entity(
            name="EDITOR",
            is_system=False,
            organization_id=self.org_id,
        )

        uow = make_uow()
        role_repo_mock = AsyncMock()
        role_repo_mock.find_one.return_value = None  # No duplicate assignment
        role_repo_mock.get_by_id.return_value = role_entity
        role_repo_mock.create.return_value = make_entity()
        uow.get_repository.return_value = role_repo_mock

        svc = RoleService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        target_user_id = uuid.uuid4()
        role_id = uuid.uuid4()

        with (
            patch("api.services.iam.role_service._RoleRepository", return_value=role_repo_mock),
            patch("api.services.iam.role_service._UserRoleRepository", return_value=role_repo_mock),
        ):
            result = await svc.assign_role_to_user(
                self.ctx,
                dto=AssignRoleDTO(
                    user_id=target_user_id,
                    role_id=role_id,
                    organization_id=self.org_id,
                ),
            )

        assert result.is_success
        assert result.data is True
        assert any(e.event_type == "iam.role.assigned" for e in uow._events)


# =============================================================================
# InvitationService Tests
# =============================================================================

class TestInvitationService:
    """Tests for InvitationService lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.org_id = self.ctx.organization_id

    @pytest.mark.asyncio
    async def test_send_invitation_success(self):
        """send_invitation() creates invitation and publishes InvitationSent event."""
        now = datetime.now(timezone.utc)
        invite_entity = make_entity(
            organization_id=self.org_id,
            invited_by=self.ctx.user_id,
            email="test@example.com",
            role="MEMBER",
            token="abc123",
            message=None,
            is_accepted=False,
            is_rejected=False,
            accepted_at=None,
            expires_at=now + timedelta(hours=72),
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = None  # No pending invite
        repo_mock.create.return_value = invite_entity
        uow.get_repository.return_value = repo_mock

        svc = InvitationService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.invitation_service._InvitationRepository", return_value=repo_mock):
            result = await svc.send_invitation(
                self.ctx,
                org_id=self.org_id,
                dto=SendInvitationDTO(email="test@example.com", role="MEMBER"),
            )

        assert result.is_success
        assert result.status_code == 201
        assert result.data.email == "test@example.com"
        assert any(e.event_type == "iam.invitation.sent" for e in uow._events)

    @pytest.mark.asyncio
    async def test_reject_invitation(self):
        """reject_invitation() marks the invitation as rejected."""
        token = "secure_token_xyz"
        now = datetime.now(timezone.utc)
        invite_entity = make_entity(
            organization_id=self.org_id,
            invited_by=None,
            email="test@example.com",
            role="MEMBER",
            token=token,
            is_accepted=False,
            is_rejected=False,
            expires_at=now + timedelta(hours=48),
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = invite_entity
        repo_mock.update.return_value = make_entity(is_rejected=True)
        uow.get_repository.return_value = repo_mock

        svc = InvitationService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.invitation_service._InvitationRepository", return_value=repo_mock):
            result = await svc.reject_invitation(self.ctx, token=token)

        assert result.is_success
        assert any(e.event_type == "iam.invitation.rejected" for e in uow._events)


# =============================================================================
# SecurityPolicyService Tests
# =============================================================================

class TestSecurityPolicyService:
    """Tests for SecurityPolicyService lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.org_id = self.ctx.organization_id

    @pytest.mark.asyncio
    async def test_create_default_policy(self):
        """create_default_policy() provisions a default SecurityPolicy."""
        from api.services.iam.constants import SECURITY_POLICY_DEFAULTS
        policy_entity = make_entity(
            organization_id=self.org_id,
            **SECURITY_POLICY_DEFAULTS,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = None  # No existing policy
        repo_mock.create.return_value = policy_entity
        uow.get_repository.return_value = repo_mock

        svc = SecurityPolicyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.security_policy_service._SecurityPolicyRepository", return_value=repo_mock):
            result = await svc.create_default_policy(self.ctx, org_id=self.org_id)

        assert result.is_success
        assert result.data.mfa_required is False
        assert result.data.max_concurrent_sessions == SECURITY_POLICY_DEFAULTS["max_concurrent_sessions"]
        assert any(e.event_type == "iam.security_policy.created" for e in uow._events)

    @pytest.mark.asyncio
    async def test_validate_password_success(self):
        """validate_password_against_policy() returns is_valid=True for a compliant password."""
        from api.services.iam.constants import SECURITY_POLICY_DEFAULTS
        policy_data = dict(SECURITY_POLICY_DEFAULTS)
        policy_data.update({
            "allowed_mfa_methods": None,
            "allowed_ip_ranges": None,
            "api_key_max_expiry_days": None,
            "api_key_require_ip_restriction": False,
            "sso_enforced": False,
        })
        policy_entity = make_entity(
            organization_id=self.org_id,
            **policy_data,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = policy_entity
        uow.get_repository.return_value = repo_mock

        svc = SecurityPolicyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.security_policy_service._SecurityPolicyRepository", return_value=repo_mock):
            result = await svc.validate_password_against_policy(
                self.ctx,
                org_id=self.org_id,
                password_plaintext="SecurePass123",
            )

        assert result.is_success
        assert result.data.is_valid is True
        assert len(result.data.violations) == 0

    @pytest.mark.asyncio
    async def test_validate_password_too_short(self):
        """validate_password_against_policy() returns violations for short password."""
        from api.services.iam.constants import SECURITY_POLICY_DEFAULTS
        policy_data = dict(SECURITY_POLICY_DEFAULTS)
        policy_data.update({
            "password_min_length": 12,
            "allowed_mfa_methods": None,
            "allowed_ip_ranges": None,
            "api_key_max_expiry_days": None,
            "api_key_require_ip_restriction": False,
            "sso_enforced": False,
        })
        policy_entity = make_entity(
            organization_id=self.org_id,
            **policy_data,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = policy_entity
        uow.get_repository.return_value = repo_mock

        svc = SecurityPolicyService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.security_policy_service._SecurityPolicyRepository", return_value=repo_mock):
            result = await svc.validate_password_against_policy(
                self.ctx,
                org_id=self.org_id,
                password_plaintext="Short1",
            )

        assert result.is_success
        assert result.data.is_valid is False
        assert any("12" in v or "length" in v.lower() for v in result.data.violations)


# =============================================================================
# OAuthService Tests
# =============================================================================

class TestOAuthService:
    """Tests for OAuthService provider linking."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cache = InMemoryCacheManager()
        self.authorizer = make_authorizer()
        self.ctx = make_ctx()
        self.user_id = self.ctx.user_id

    @pytest.mark.asyncio
    async def test_link_oauth_account(self):
        """link_oauth_account() creates a linked account and publishes OAuthAccountLinked."""
        oauth_entity = make_entity(
            user_id=self.user_id,
            provider="google",
            provider_user_id="google_uid_123",
            provider_email="user@gmail.com",
            token_expires_at=None,
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = None  # Not already linked, not taken
        repo_mock.create.return_value = oauth_entity
        uow.get_repository.return_value = repo_mock

        svc = OAuthService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.oauth_service._OAuthAccountRepository", return_value=repo_mock):
            result = await svc.link_oauth_account(
                self.ctx,
                user_id=self.user_id,
                dto=LinkOAuthAccountDTO(
                    provider="google",
                    provider_user_id="google_uid_123",
                    provider_email="user@gmail.com",
                ),
            )

        assert result.is_success
        assert result.status_code == 201
        assert result.data.provider == "google"
        assert any(e.event_type == "iam.oauth.account_linked" for e in uow._events)

    @pytest.mark.asyncio
    async def test_link_duplicate_provider_raises_conflict(self):
        """link_oauth_account() fails with ConflictError if provider already linked."""
        existing_account = make_entity(
            user_id=self.user_id,
            provider="google",
            provider_user_id="google_uid_123",
        )

        uow = make_uow()
        repo_mock = AsyncMock()
        repo_mock.find_one.return_value = existing_account  # Already linked
        uow.get_repository.return_value = repo_mock

        svc = OAuthService(
            uow_service=uow,
            cache_manager=self.cache,
            authorizer=self.authorizer,
        )

        with patch("api.services.iam.oauth_service._OAuthAccountRepository", return_value=repo_mock):
            result = await svc.link_oauth_account(
                self.ctx,
                user_id=self.user_id,
                dto=LinkOAuthAccountDTO(
                    provider="google",
                    provider_user_id="google_uid_123",
                ),
            )

        assert result.is_failure
        assert "already" in result.errors[0].lower()
