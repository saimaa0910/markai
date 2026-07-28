"""
EAIMOS IAM Dependency Providers
==================================
FastAPI-compatible dependency injection providers for all Sprint 2 IAM services.
Each `get_*_service()` function returns a fully wired service instance
with repositories, UoW, authorizer, cache, and dispatcher resolved.
"""

from typing import Annotated

from api.services.base.authorization import AuthorizationService
from api.services.base.cache import InMemoryCacheManager
from api.services.base.dependency_provider import container
from api.services.base.event_dispatcher import EventDispatcher
from api.services.base.unit_of_work_service import UnitOfWorkService
from api.services.iam.session_service import SessionService
from api.services.iam.api_key_service import APIKeyService
from api.services.iam.role_service import RoleService
from api.services.iam.invitation_service import InvitationService
from api.services.iam.security_policy_service import SecurityPolicyService
from api.services.iam.oauth_service import OAuthService


# ─── Shared Infrastructure Providers ─────────────────────────────────────────

def get_uow_service() -> UnitOfWorkService:
    """Provide a fresh UnitOfWorkService from the DI container."""
    return container.create_uow_service()


def get_authorizer() -> AuthorizationService:
    """Provide the platform-wide AuthorizationService instance."""
    return container.authorizer


def get_cache():
    """Provide the configured cache manager (Redis in prod, in-memory in tests)."""
    return container.cache


def get_dispatcher() -> EventDispatcher:
    """Provide the configured domain event dispatcher."""
    return container.dispatcher


# ─── IAM Service Providers ────────────────────────────────────────────────────

def get_session_service() -> SessionService:
    """
    Provide a fully initialized SessionService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return SessionService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )


def get_api_key_service() -> APIKeyService:
    """
    Provide a fully initialized APIKeyService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return APIKeyService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )


def get_role_service() -> RoleService:
    """
    Provide a fully initialized RoleService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return RoleService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )


def get_invitation_service() -> InvitationService:
    """
    Provide a fully initialized InvitationService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return InvitationService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )


def get_security_policy_service() -> SecurityPolicyService:
    """
    Provide a fully initialized SecurityPolicyService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return SecurityPolicyService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )


def get_oauth_service() -> OAuthService:
    """
    Provide a fully initialized OAuthService.
    Injects: UnitOfWork, cache, authorizer, event dispatcher.
    """
    return OAuthService(
        uow_service=get_uow_service(),
        cache_manager=get_cache(),
        authorizer=get_authorizer(),
        dispatcher=get_dispatcher(),
    )
