"""
EAIMOS User Service Module (Sprint 1: Core Platform)
=====================================================
Service Layer managing user registration, profile updates, status toggles, email verification,
and authorization context verification.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, EmailStr, Field

from api.models.user import User
from api.repositories.user_repository import UserRepository
from api.services.base import (
    BaseService,
    ConflictError,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
    ValidationError,
)


# ── User DTOs ──────────────────────────────────────────────────────────────────

class CreateUserDTO(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password_hash: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    timezone: str = "UTC"
    locale: str = "en-US"


class UpdateUserDTO(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class UserService(BaseService[User, CreateUserDTO, UpdateUserDTO, User]):
    """
    Enterprise User Domain Service.
    Coordinates platform user registration, profile settings, and email lookups.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        authorizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            repository_cls=UserRepository,
            uow_service=uow_service,
            cache_manager=cache_manager,
            dispatcher=dispatcher,
            authorizer=authorizer,
            entity_name="User",
            read_permission=EnterprisePermission.IAM_USER_READ.value,
            write_permission=EnterprisePermission.IAM_USER_WRITE.value,
        )

    async def before_create(self, ctx: ServiceContext, dto: CreateUserDTO) -> None:
        """Prevent duplicate user registration by email."""
        clean_email = dto.email.lower().strip()
        async with self.uow_service:
            repo = self.uow_service.get_repository(UserRepository)
            existing = await repo.get_by_email(self.uow_service.session, clean_email)
            if existing:
                raise ConflictError(
                    message=f"User with email '{clean_email}' already exists.",
                    error_code="EMAIL_ALREADY_EXISTS",
                )

    async def get_by_email(self, ctx: ServiceContext, email: str) -> ServiceResult[Optional[User]]:
        """Lookup user by email address."""
        try:
            self._verify_read_permission(ctx)
            clean_email = email.lower().strip()
            cache_key = f"user:email:{clean_email}"

            cached_val = await self.cache.get(cache_key)
            if cached_val is not None:
                return ServiceResult.ok(data=cached_val, metadata={"cached": True})

            async with self.uow_service:
                repo = self.uow_service.get_repository(UserRepository)
                user = await repo.get_by_email(self.uow_service.session, clean_email)
                if not user:
                    return ServiceResult.fail(
                        error=f"User with email '{clean_email}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )
                return ServiceResult.ok(data=user)

        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def update_status(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        is_active: bool,
    ) -> ServiceResult[User]:
        """Activate or deactivate user account."""
        try:
            self.authorizer.require_permission(ctx, EnterprisePermission.IAM_USER_WRITE.value)
            update_dto = UpdateUserDTO(is_active=is_active)
            return await self.update(ctx, id=user_id, dto=update_dto)
        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def verify_email(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[User]:
        """Mark user's email address as verified."""
        try:
            update_dto = UpdateUserDTO(is_verified=True)
            return await self.update(ctx, id=user_id, dto=update_dto)
        except Exception as exc:
            return ServiceResult.from_exception(exc)
