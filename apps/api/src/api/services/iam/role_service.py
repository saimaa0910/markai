"""
EAIMOS IAM Role Service (Sprint 2)
=====================================
Manages the full RBAC role lifecycle: creation of org-scoped custom roles,
permission assignment via role_permissions_junction, time-limited role grants to users,
system role immutability enforcement, and effective permission resolution.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.iam import Permission, Role, UserRole
from api.repositories.iam_repository import (  # type: ignore[attr-defined]
    UserSessionRepository,
)
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterOperator, FilterParam
from api.services.base import (
    ConflictError,
    EnterprisePermission,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.base.service_exceptions import BusinessRuleViolation, ForbiddenOperation
from api.services.iam.cache_keys import (
    ROLE_KEY_TTL,
    USER_ROLES_KEY_TTL,
    PERMISSION_KEY_TTL,
    invalidate_pattern_for_org_roles,
    invalidate_pattern_for_user_permissions,
    org_roles_list_key,
    role_cache_key,
    user_roles_cache_key,
    user_permissions_cache_key,
)
from api.services.iam.dtos import (
    AssignPermissionToRoleDTO,
    AssignRoleDTO,
    CreatePermissionDTO,
    CreateRoleDTO,
    EffectivePermissionsDTO,
    PermissionResponseDTO,
    RoleListDTO,
    RoleResponseDTO,
    RoleSummaryDTO,
    RevokeRoleDTO,
    UpdateRoleDTO,
    UserRoleResponseDTO,
)
from api.services.iam.events import (
    PermissionAssignedToRole,
    PermissionRemovedFromRole,
    RoleAssigned,
    RoleCreated,
    RoleDeleted,
    RoleRevoked,
    RoleUpdated,
)
from api.services.iam.mappers import (
    build_effective_permissions_dto,
    permission_to_response_dto,
    role_to_response_dto,
    role_to_summary_dto,
    roles_to_summary_list,
    user_role_to_response_dto,
)
from api.services.iam.policies import RolePolicy
from api.services.iam.validators import (
    validate_role_name_format,
    validate_role_not_assigned_to_users,
    validate_role_not_expired,
    validate_role_not_system,
    validate_user_role_not_duplicate,
)

logger = logging.getLogger("eaimos.iam.role")


class _RoleRepository(BaseRepository[Role]):
    def __init__(self) -> None:
        super().__init__(Role)


class _PermissionRepository(BaseRepository[Permission]):
    def __init__(self) -> None:
        super().__init__(Permission)


class _UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self) -> None:
        super().__init__(UserRole)


class RoleService:
    """
    Enterprise IAM Role Domain Service.

    Manages custom role creation, permission assignments, user role grants,
    effective permission resolution, and system role immutability enforcement.
    """

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        authorizer: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher

    # ─── Create Role ──────────────────────────────────────────────────────────

    async def create_role(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]:
        """Create a custom org-scoped role."""
        try:
            RolePolicy.can_create(self.authorizer, ctx, org_id)
            validate_role_name_format(dto.name)

            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _RoleRepository()

                # Duplicate name check within org
                existing = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="name", operator=FilterOperator.EQ, value=dto.name),
                        FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid),
                    ],
                )
                if existing:
                    raise ConflictError(
                        message=f"Role '{dto.name}' already exists in this organization.",
                        error_code="ROLE_NAME_EXISTS",
                    )

                role_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "name": dto.name,
                    "display_name": dto.display_name,
                    "description": dto.description,
                    "is_system": False,
                    "is_default": dto.is_default,
                    "metadata_json": dto.metadata_json,
                }

                role = await repo.create(
                    session=self.uow_service.session,
                    obj_in=role_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    RoleCreated(
                        aggregate_id=str(role.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(role.id),
                        role_name=dto.name,
                        is_system=False,
                        payload={"role_id": str(role.id), "role_name": dto.name},
                    )
                )

            # Invalidate org roles cache
            await self.cache.delete_pattern(invalidate_pattern_for_org_roles(org_id))

            response = role_to_response_dto(role, include_permissions=True)
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_role failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get Role ─────────────────────────────────────────────────────────────

    async def get_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
    ) -> ServiceResult[RoleResponseDTO]:
        """Retrieve a role by ID with cache-first lookup."""
        try:
            RolePolicy.can_read(self.authorizer, ctx)

            cache_key = role_cache_key(role_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=RoleResponseDTO(**cached),
                    metadata={"cached": True},
                )

            async with self.uow_service:
                repo = _RoleRepository()
                role = await repo.get_by_id(session=self.uow_service.session, id=role_id)
                if not role:
                    return ServiceResult.fail(
                        error=f"Role '{role_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Tenant isolation — org-custom roles require membership check
                if role.organization_id:
                    RolePolicy.can_read(self.authorizer, ctx, org_id=role.organization_id)

                response = role_to_response_dto(role, include_permissions=True)
                await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=ROLE_KEY_TTL)
                return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_role failed for {role_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── List Roles ───────────────────────────────────────────────────────────

    async def list_roles(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        include_system: bool = True,
        page: int = 1,
        page_size: int = 50,
    ) -> ServiceResult[RoleListDTO]:
        """Return all roles available to an organization (system + org-custom)."""
        try:
            RolePolicy.can_read(self.authorizer, ctx, org_id=org_id)

            org_uuid = uuid.UUID(str(org_id))
            async with self.uow_service:
                repo = _RoleRepository()

                filters: List[FilterParam] = []
                if not include_system:
                    filters.append(FilterParam(field="is_system", operator=FilterOperator.EQ, value=False))

                # Get both system roles (organization_id IS NULL) and org-specific ones
                all_roles = await repo.find_many(session=self.uow_service.session, filters=filters)
                org_roles = [r for r in all_roles if r.organization_id is None or str(r.organization_id) == str(org_uuid)]

            total = len(org_roles)
            start = (page - 1) * page_size
            paginated = org_roles[start: start + page_size]
            summaries = roles_to_summary_list(paginated)

            return ServiceResult.ok(
                data=RoleListDTO(
                    items=summaries,
                    total=total,
                    page=page,
                    page_size=page_size,
                )
            )

        except Exception as exc:
            logger.error(f"list_roles failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Update Role ──────────────────────────────────────────────────────────

    async def update_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        dto: UpdateRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]:
        """Update metadata of a custom org role. System roles are immutable."""
        try:
            async with self.uow_service:
                repo = _RoleRepository()
                role = await repo.get_by_id(session=self.uow_service.session, id=role_id)
                if not role:
                    return ServiceResult.fail(
                        error=f"Role '{role_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                RolePolicy.can_update(self.authorizer, ctx, org_id=role.organization_id or ctx.organization_id)
                validate_role_not_system(role.is_system, role.name, "updated")

                update_data = dto.model_dump(exclude_unset=True)
                updated = await repo.update(
                    session=self.uow_service.session,
                    id=role_id,
                    obj_in=update_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    RoleUpdated(
                        aggregate_id=str(role_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(role_id),
                        role_name=role.name,
                        changes=update_data,
                        payload={"role_id": str(role_id), "changes": update_data},
                    )
                )

            await self.cache.delete(role_cache_key(role_id))
            if role.organization_id:
                await self.cache.delete_pattern(invalidate_pattern_for_org_roles(role.organization_id))

            return ServiceResult.ok(data=role_to_response_dto(updated, include_permissions=True))

        except Exception as exc:
            logger.error(f"update_role failed for {role_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Delete Role ──────────────────────────────────────────────────────────

    async def delete_role(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
    ) -> ServiceResult[bool]:
        """Soft-delete a custom role after verifying no active assignments."""
        try:
            async with self.uow_service:
                repo = _RoleRepository()
                role = await repo.get_by_id(session=self.uow_service.session, id=role_id)
                if not role:
                    return ServiceResult.fail(
                        error=f"Role '{role_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                RolePolicy.can_delete(self.authorizer, ctx, org_id=role.organization_id or ctx.organization_id)
                validate_role_not_system(role.is_system, role.name, "deleted")

                # Check for active UserRole assignments
                user_role_repo = _UserRoleRepository()
                assignments = await user_role_repo.find_many(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="role_id", operator=FilterOperator.EQ, value=uuid.UUID(str(role_id)))],
                )
                validate_role_not_assigned_to_users(len(assignments), str(role_id))

                await repo.soft_delete(
                    session=self.uow_service.session,
                    id=role_id,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    RoleDeleted(
                        aggregate_id=str(role_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(role_id),
                        role_name=role.name,
                        payload={"role_id": str(role_id), "role_name": role.name},
                    )
                )

            await self.cache.delete(role_cache_key(role_id))
            if role.organization_id:
                await self.cache.delete_pattern(invalidate_pattern_for_org_roles(role.organization_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"delete_role failed for {role_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Assign Permission to Role ────────────────────────────────────────────

    async def assign_permission(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        dto: AssignPermissionToRoleDTO,
    ) -> ServiceResult[RoleResponseDTO]:
        """Add a permission to a role via the role_permissions_junction table."""
        try:
            async with self.uow_service:
                role_repo = _RoleRepository()
                role = await role_repo.get_by_id(session=self.uow_service.session, id=role_id)
                if not role:
                    return ServiceResult.fail(
                        error=f"Role '{role_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                RolePolicy.can_update(self.authorizer, ctx, org_id=role.organization_id or ctx.organization_id)
                validate_role_not_system(role.is_system, role.name, "modified")

                perm_repo = _PermissionRepository()
                permission = await perm_repo.get_by_id(
                    session=self.uow_service.session,
                    id=dto.permission_id,
                )
                if not permission:
                    return ServiceResult.fail(
                        error=f"Permission '{dto.permission_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Prevent duplicate assignment (junction table handles unique constraint)
                if permission not in role.permissions:
                    role.permissions.append(permission)

                self.uow_service.add_event(
                    PermissionAssignedToRole(
                        aggregate_id=str(role_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(role_id),
                        permission_id=str(dto.permission_id),
                        permission_label=f"{permission.resource}:{permission.action}:{permission.scope}",
                        payload={"role_id": str(role_id), "permission_id": str(dto.permission_id)},
                    )
                )

            await self.cache.delete(role_cache_key(role_id))
            await self.cache.delete_pattern(invalidate_pattern_for_user_permissions("*"))

            updated_role = await self._reload_role(role_id)
            return ServiceResult.ok(data=role_to_response_dto(updated_role, include_permissions=True))

        except Exception as exc:
            logger.error(f"assign_permission failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Remove Permission from Role ──────────────────────────────────────────

    async def remove_permission(
        self,
        ctx: ServiceContext,
        role_id: Union[uuid.UUID, str],
        permission_id: Union[uuid.UUID, str],
    ) -> ServiceResult[RoleResponseDTO]:
        """Remove a permission from a role."""
        try:
            async with self.uow_service:
                role_repo = _RoleRepository()
                role = await role_repo.get_by_id(session=self.uow_service.session, id=role_id)
                if not role:
                    return ServiceResult.fail(
                        error=f"Role '{role_id}' not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                RolePolicy.can_update(self.authorizer, ctx, org_id=role.organization_id or ctx.organization_id)
                validate_role_not_system(role.is_system, role.name, "modified")

                perm_to_remove = next(
                    (p for p in role.permissions if str(p.id) == str(permission_id)),
                    None,
                )
                if perm_to_remove:
                    role.permissions.remove(perm_to_remove)
                    label = f"{perm_to_remove.resource}:{perm_to_remove.action}:{perm_to_remove.scope}"
                else:
                    label = str(permission_id)

                self.uow_service.add_event(
                    PermissionRemovedFromRole(
                        aggregate_id=str(role_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(role_id),
                        permission_id=str(permission_id),
                        permission_label=label,
                        payload={"role_id": str(role_id), "permission_id": str(permission_id)},
                    )
                )

            await self.cache.delete(role_cache_key(role_id))
            await self.cache.delete_pattern(invalidate_pattern_for_user_permissions("*"))

            updated_role = await self._reload_role(role_id)
            return ServiceResult.ok(data=role_to_response_dto(updated_role, include_permissions=True))

        except Exception as exc:
            logger.error(f"remove_permission failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Assign Role to User ──────────────────────────────────────────────────

    async def assign_role_to_user(
        self,
        ctx: ServiceContext,
        dto: AssignRoleDTO,
    ) -> ServiceResult[bool]:
        """Grant a role to a user within an organization (time-limited grants supported)."""
        try:
            RolePolicy.can_assign(self.authorizer, ctx, dto.organization_id)

            async with self.uow_service:
                ur_repo = _UserRoleRepository()

                # Duplicate check
                existing = await ur_repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=dto.user_id),
                        FilterParam(field="role_id", operator=FilterOperator.EQ, value=dto.role_id),
                        FilterParam(field="organization_id", operator=FilterOperator.EQ, value=dto.organization_id),
                    ],
                )
                validate_user_role_not_duplicate(
                    existing is not None,
                    str(dto.user_id),
                    str(dto.role_id),
                    str(dto.organization_id),
                )

                # Load role name for event
                role_repo = _RoleRepository()
                role = await role_repo.get_by_id(session=self.uow_service.session, id=dto.role_id)
                role_name = role.name if role else str(dto.role_id)

                assignment_data: Dict[str, Any] = {
                    "user_id": str(dto.user_id),
                    "role_id": str(dto.role_id),
                    "organization_id": str(dto.organization_id),
                    "granted_by": ctx.get_user_id_str(),
                    "expires_at": dto.expires_at,
                }

                await ur_repo.create(
                    session=self.uow_service.session,
                    obj_in=assignment_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    RoleAssigned(
                        aggregate_id=str(dto.user_id),
                        tenant_id=str(dto.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(dto.role_id),
                        role_name=role_name,
                        target_user_id=str(dto.user_id),
                        granted_by=ctx.get_user_id_str(),
                        expires_at=dto.expires_at.isoformat() if dto.expires_at else None,
                        payload={"user_id": str(dto.user_id), "role_id": str(dto.role_id)},
                    )
                )

            await self.cache.delete(user_roles_cache_key(dto.user_id, dto.organization_id))
            await self.cache.delete(user_permissions_cache_key(dto.user_id, dto.organization_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"assign_role_to_user failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Revoke Role from User ────────────────────────────────────────────────

    async def revoke_role_from_user(
        self,
        ctx: ServiceContext,
        dto: RevokeRoleDTO,
    ) -> ServiceResult[bool]:
        """Remove a role assignment from a user."""
        try:
            RolePolicy.can_revoke(self.authorizer, ctx, dto.organization_id)

            async with self.uow_service:
                ur_repo = _UserRoleRepository()
                assignment = await ur_repo.find_one(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=dto.user_id),
                        FilterParam(field="role_id", operator=FilterOperator.EQ, value=dto.role_id),
                        FilterParam(field="organization_id", operator=FilterOperator.EQ, value=dto.organization_id),
                    ],
                )
                if not assignment:
                    return ServiceResult.fail(
                        error="Role assignment not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                role_repo = _RoleRepository()
                role = await role_repo.get_by_id(session=self.uow_service.session, id=dto.role_id)
                role_name = role.name if role else str(dto.role_id)

                await ur_repo.hard_delete(session=self.uow_service.session, id=assignment.id)

                self.uow_service.add_event(
                    RoleRevoked(
                        aggregate_id=str(dto.user_id),
                        tenant_id=str(dto.organization_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        role_id=str(dto.role_id),
                        role_name=role_name,
                        target_user_id=str(dto.user_id),
                        revoked_by=ctx.get_user_id_str(),
                        payload={"user_id": str(dto.user_id), "role_id": str(dto.role_id)},
                    )
                )

            await self.cache.delete(user_roles_cache_key(dto.user_id, dto.organization_id))
            await self.cache.delete(user_permissions_cache_key(dto.user_id, dto.organization_id))

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"revoke_role_from_user failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get Effective Permissions ────────────────────────────────────────────

    async def get_effective_permissions(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[EffectivePermissionsDTO]:
        """Resolve the complete permission set for a user within an org."""
        try:
            cache_key = user_permissions_cache_key(user_id, org_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=EffectivePermissionsDTO(**cached),
                    metadata={"cached": True},
                )

            async with self.uow_service:
                ur_repo = _UserRoleRepository()
                assignments = await ur_repo.find_many(
                    session=self.uow_service.session,
                    filters=[
                        FilterParam(field="user_id", operator=FilterOperator.EQ, value=uuid.UUID(str(user_id))),
                        FilterParam(field="organization_id", operator=FilterOperator.EQ, value=uuid.UUID(str(org_id))),
                    ],
                )

            is_super = ctx.is_super_admin if str(ctx.user_id) == str(user_id) else False
            result = build_effective_permissions_dto(
                user_id=str(user_id),
                org_id=str(org_id),
                role_assignments=assignments,
                is_super_admin=is_super,
            )

            await self.cache.set(
                cache_key,
                result.model_dump(mode="json"),
                ttl=USER_ROLES_KEY_TTL,
            )
            return ServiceResult.ok(data=result)

        except Exception as exc:
            logger.error(f"get_effective_permissions failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    async def _reload_role(self, role_id: Union[uuid.UUID, str]) -> Any:
        """Reload a role with eager-loaded permissions after a mutation."""
        async with self.uow_service:
            repo = _RoleRepository()
            return await repo.get_by_id(session=self.uow_service.session, id=role_id)
