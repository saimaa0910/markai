"""
EAIMOS Organization Membership Service Module (Sprint 1: Core Platform)
========================================================================
Service Layer managing tenant seat assignments, user-organization memberships,
role assignments, and seat quota enforcement.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field

from api.models.membership import UserOrganization, UserRole
from api.models.organization import Organization
from api.repositories.membership_repository import UserOrganizationRepository
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
)


# ── Membership DTOs ─────────────────────────────────────────────────────────────

class CreateMembershipDTO(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str = Field("MEMBER", description="OWNER | ADMIN | MEMBER | GUEST")
    job_title: Optional[str] = None


class UpdateMembershipDTO(BaseModel):
    role: Optional[str] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None


class UserOrganizationService(BaseService[UserOrganization, CreateMembershipDTO, UpdateMembershipDTO, UserOrganization]):
    """
    Enterprise Organization Membership Domain Service.
    Coordinates member additions, role assignments, seat quotas, and member removal.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        authorizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            repository_cls=UserOrganizationRepository,
            uow_service=uow_service,
            cache_manager=cache_manager,
            dispatcher=dispatcher,
            authorizer=authorizer,
            entity_name="UserOrganization",
            read_permission=EnterprisePermission.IAM_USER_READ.value,
            write_permission=EnterprisePermission.IAM_ROLE_MANAGE.value,
        )

    def _get_tenant_repo(self, org_id: uuid.UUID) -> UserOrganizationRepository:
        """Instantiate UserOrganizationRepository for a specific organization."""
        return UserOrganizationRepository(organization_id=org_id)

    async def add_member(
        self,
        ctx: ServiceContext,
        dto: CreateMembershipDTO,
    ) -> ServiceResult[UserOrganization]:
        """Add a new member to an organization after seat quota validation."""
        try:
            allowed_roles = {"OWNER", "ADMIN", "MEMBER", "GUEST"}
            role_upper = dto.role.upper()
            if role_upper not in allowed_roles:
                raise ValidationError(
                    message=f"Invalid membership role '{dto.role}'. Allowed roles: {allowed_roles}"
                )
            self.authorizer.require_tenant_access(ctx, dto.organization_id)
            self.authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

            async with self.uow_service:
                org_repo = self.uow_service.get_repository(OrganizationRepository)
                org = await org_repo.get_by_id(self.uow_service.session, dto.organization_id)
                if not org:
                    raise NotFoundError(message=f"Organization '{dto.organization_id}' not found.")

                member_repo = self._get_tenant_repo(dto.organization_id)
                current_member_count = await member_repo.count_by_org(
                    self.uow_service.session,
                    dto.organization_id,
                )

                if current_member_count >= org.max_members:
                    raise BusinessRuleViolation(
                        message=f"Seat limit reached ({org.max_members}). Upgrade plan to add more members.",
                        rule_name="ORGANIZATION_SEAT_QUOTA_EXCEEDED",
                    )

                # Check if user is already a member
                existing_member = await member_repo.get_user_membership(
                    self.uow_service.session,
                    dto.user_id,
                )
                if existing_member:
                    raise ConflictError(
                        message=f"User '{dto.user_id}' is already a member of this organization.",
                        error_code="MEMBER_ALREADY_EXISTS",
                    )

                membership = await member_repo.create(
                    session=self.uow_service.session,
                    obj_in={
                        "user_id": dto.user_id,
                        "organization_id": dto.organization_id,
                        "role": dto.role.upper(),
                        "job_title": dto.job_title,
                    },
                    actor_id=ctx.get_user_id_str(),
                )

            # Invalidate org member list cache
            await self.cache.delete(f"org:{dto.organization_id}:members")
            return ServiceResult.ok(data=membership, status_code=201)

        except Exception as exc:
            return ServiceResult.from_exception(exc)

    async def get_org_members(
        self,
        ctx: ServiceContext,
        organization_id: Union[uuid.UUID, str],
        limit: int = 50,
        offset: int = 0,
    ) -> ServiceResult[List[UserOrganization]]:
        """List active members of a tenant organization."""
        try:
            org_id_uuid = uuid.UUID(str(organization_id))
            self.authorizer.require_tenant_access(ctx, org_id_uuid)

            async with self.uow_service:
                repo = self._get_tenant_repo(org_id_uuid)
                members = await repo.list_organization_members(
                    session=self.uow_service.session,
                    limit=limit,
                    offset=offset,
                )
                return ServiceResult.ok(data=members)

        except Exception as exc:
            return ServiceResult.from_exception(exc)
