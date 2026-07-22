"""
EAIMOS Organization Service Module (Sprint 1: Core Platform)
============================================================
Service Layer handling tenant organization management, plan tier updates,
resource quota verification, unique slug lookups, and multi-tenant scoping.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field

from api.models.organization import Organization
from api.repositories.filters import FilterParam, FilterOperator
from api.repositories.organization_repository import OrganizationRepository
from api.services.base import (
    BaseService,
    BusinessRuleViolation,
    ConflictError,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
    ValidationError,
    ValidatorChain,
)


# ── Organization DTOs ──────────────────────────────────────────────────────────

class CreateOrganizationDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    plan_tier: str = Field("free", description="free | starter | professional | enterprise")
    max_members: int = Field(5, ge=1)
    max_ai_credits: float = Field(100.0, ge=0.0)
    max_storage_gb: int = Field(5, ge=1)
    billing_email: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country_code: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en-US"


class UpdateOrganizationDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    plan_tier: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1)
    max_ai_credits: Optional[float] = Field(None, ge=0.0)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    billing_email: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class OrganizationService(BaseService[Organization, CreateOrganizationDTO, UpdateOrganizationDTO, Organization]):
    """
    Enterprise Organization Domain Service.
    Coordinates tenant boundary lifecycle, tier upgrades, quota checks, and slug lookups.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        authorizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            repository_cls=OrganizationRepository,
            uow_service=uow_service,
            cache_manager=cache_manager,
            dispatcher=dispatcher,
            authorizer=authorizer,
            entity_name="Organization",
            read_permission=EnterprisePermission.IAM_ORG_READ.value,
            write_permission=EnterprisePermission.IAM_ORG_WRITE.value,
        )

    async def before_create(self, ctx: ServiceContext, dto: CreateOrganizationDTO) -> None:
        """Validate tier values and check unique slug existence."""
        allowed_tiers = {"free", "starter", "professional", "enterprise"}
        if dto.plan_tier.lower() not in allowed_tiers:
            raise ValidationError(
                message=f"Invalid plan tier '{dto.plan_tier}'. Allowed tiers: {allowed_tiers}",
                field_errors=[{"field": "plan_tier", "message": "Invalid tier"}],
            )

        # Check unique slug
        async with self.uow_service:
            repo = self.uow_service.get_repository(OrganizationRepository)
            existing = await repo.get_by_slug(self.uow_service.session, dto.slug.lower())
            if existing:
                raise ConflictError(
                    message=f"Organization with slug '{dto.slug}' already exists.",
                    error_code="SLUG_ALREADY_EXISTS",
                )

    async def get_by_slug(self, ctx: ServiceContext, slug: str) -> ServiceResult[Optional[Organization]]:
        """Lookup tenant organization by unique slug."""
        try:
            self._verify_read_permission(ctx)
            cache_key = f"org:slug:{slug.lower()}"

            cached_val = await self.cache.get(cache_key)
            if cached_val is not None:
                return ServiceResult.ok(data=cached_val, metadata={"cached": True})

            async with self.uow_service:
                repo = self.uow_service.get_repository(OrganizationRepository)
                org = await repo.get_by_slug(self.uow_service.session, slug.lower())
                if not org:
                    return ServiceResult.fail(
                        error=f"Organization with slug '{slug}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                return ServiceResult.ok(data=org)

        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def update_tier(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        new_tier: str,
        max_members: Optional[int] = None,
        max_ai_credits: Optional[float] = None,
    ) -> ServiceResult[Organization]:
        """Upgrade or downgrade tenant subscription plan tier."""
        try:
            self.authorizer.require_permission(ctx, EnterprisePermission.BILLING_MANAGE.value)
            allowed_tiers = {"free", "starter", "professional", "enterprise"}
            if new_tier.lower() not in allowed_tiers:
                raise ValidationError(message=f"Invalid tier '{new_tier}'")

            async with self.uow_service:
                repo = self.uow_service.get_repository(OrganizationRepository)
                org = await repo.update_tier(
                    session=self.uow_service.session,
                    org_id=uuid.UUID(str(org_id)),
                    new_tier=new_tier.lower(),
                    max_members=max_members,
                    max_ai_credits=max_ai_credits,
                )

            # Invalidate cache
            await self.cache.delete(f"org:{str(org_id)}")
            return ServiceResult.ok(data=org)

        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def get_active_organizations(
        self,
        ctx: ServiceContext,
        limit: int = 50,
        offset: int = 0,
    ) -> ServiceResult[List[Organization]]:
        """Retrieve active non-suspended tenant organizations."""
        try:
            self.authorizer.require_permission(ctx, EnterprisePermission.ADMIN_SYSTEM.value)
            async with self.uow_service:
                repo = self.uow_service.get_repository(OrganizationRepository)
                orgs = await repo.get_active_organizations(
                    session=self.uow_service.session,
                    limit=limit,
                    offset=offset,
                )
                return ServiceResult.ok(data=orgs)
        except Exception as exc:
            return ServiceResult.from_exception(exc)
