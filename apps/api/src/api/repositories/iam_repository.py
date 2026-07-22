"""
EAIMOS IAM Repository Module — Sprint 2
=======================================
Repository implementations for Identity & Access Management models:
UserSession, PasswordResetToken, APIKey, OAuthAccount, SecurityPolicy, OrganizationInvitation.
"""

from typing import Any, List, Optional
import uuid

from api.models.iam import (
    UserSession,
    PasswordResetToken,
    APIKey,
    OAuthAccount,
    SecurityPolicy,
)
from api.models.membership import OrganizationInvitation
from api.repositories.base import BaseRepository
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class UserSessionRepository(BaseRepository[UserSession]):
    """Data access layer for active user sessions."""

    def __init__(self) -> None:
        super().__init__(UserSession)

    async def get_by_session_token(self, session: Any, session_token: str) -> Optional[UserSession]:
        filters = [FilterParam(field="session_token", operator=FilterOperator.EQ, value=session_token)]
        return await self.find_one(session=session, filters=filters)

    async def list_user_sessions(self, session: Any, user_id: uuid.UUID) -> List[UserSession]:
        filters = [FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_id)]
        return await self.find_many(session=session, filters=filters)


class APIKeyRepository(TenantRepository[APIKey]):
    """Data access layer for organization API keys."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(APIKey, organization_id=organization_id)

    async def get_by_key_hash(self, session: Any, key_hash: str) -> Optional[APIKey]:
        filters = [FilterParam(field="key_hash", operator=FilterOperator.EQ, value=key_hash)]
        return await self.find_one(session=session, filters=filters)


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Data access layer for password reset tokens."""

    def __init__(self) -> None:
        super().__init__(PasswordResetToken)

    async def get_by_token(self, session: Any, token: str) -> Optional[PasswordResetToken]:
        filters = [FilterParam(field="token", operator=FilterOperator.EQ, value=token)]
        return await self.find_one(session=session, filters=filters)


class OAuthAccountRepository(BaseRepository[OAuthAccount]):
    """Data access layer for connected OAuth provider accounts."""

    def __init__(self) -> None:
        super().__init__(OAuthAccount)

    async def get_by_provider(
        self, session: Any, provider: str, provider_user_id: str
    ) -> Optional[OAuthAccount]:
        filters = [
            FilterParam(field="provider", operator=FilterOperator.EQ, value=provider),
            FilterParam(field="provider_user_id", operator=FilterOperator.EQ, value=provider_user_id),
        ]
        return await self.find_one(session=session, filters=filters)


class OrganizationInvitationRepository(TenantRepository[OrganizationInvitation]):
    """Data access layer for organization invitations."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(OrganizationInvitation, organization_id=organization_id)

    async def get_by_token(self, session: Any, token: str) -> Optional[OrganizationInvitation]:
        filters = [FilterParam(field="token", operator=FilterOperator.EQ, value=token)]
        return await self.find_one(session=session, filters=filters)
