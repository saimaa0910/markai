"""
EAIMOS IAM Security Policy Service (Sprint 2)
==============================================
Manages per-organization security enforcement policy:
MFA enforcement, password complexity rules, session timeouts,
concurrent session limits, lockout thresholds, IP allowlists, and SSO enforcement.
Auto-provisions a default policy when an organization is created.
"""

import ipaddress
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from api.models.iam import SecurityPolicy
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterOperator, FilterParam
from api.services.base import (
    ConflictError,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.base.service_exceptions import BusinessRuleViolation
from api.services.iam.cache_keys import (
    SECURITY_POLICY_KEY_TTL,
    security_policy_cache_key,
)
from api.services.iam.constants import SECURITY_POLICY_DEFAULTS
from api.services.iam.dtos import (
    IPCheckResultDTO,
    PasswordValidationResultDTO,
    SecurityPolicyResponseDTO,
    UpdateSecurityPolicyDTO,
)
from api.services.iam.events import (
    SecurityPolicyCreated,
    SecurityPolicyIPRestrictionChanged,
    SecurityPolicyMFADisabled,
    SecurityPolicyMFAEnabled,
    SecurityPolicySSOEnforced,
    SecurityPolicyUpdated,
)
from api.services.iam.mappers import security_policy_to_response_dto
from api.services.iam.policies import SecurityPolicyPolicy
from api.services.iam.validators import (
    validate_password_against_policy,
    validate_security_policy_not_looser_than_platform,
)

logger = logging.getLogger("eaimos.iam.security_policy")


class _SecurityPolicyRepository(BaseRepository[SecurityPolicy]):
    def __init__(self) -> None:
        super().__init__(SecurityPolicy)


class SecurityPolicyService:
    """
    Enterprise IAM Security Policy Domain Service.

    1:1 with organization — every org has exactly one SecurityPolicy.
    Platform floor constraints are enforced: orgs can tighten rules but never loosen
    beyond the platform minimum (e.g., password_min_length >= 6).
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

    # ─── Create Default Policy ────────────────────────────────────────────────

    async def create_default_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SecurityPolicyResponseDTO]:
        """
        Auto-provision a default security policy for a newly created organization.
        Called from OrganizationService.after_create().
        """
        try:
            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _SecurityPolicyRepository()

                # Check if policy already exists (idempotent)
                existing = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid)],
                )
                if existing:
                    return ServiceResult.ok(data=security_policy_to_response_dto(existing))

                policy_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    **SECURITY_POLICY_DEFAULTS,
                }

                policy = await repo.create(
                    session=self.uow_service.session,
                    obj_in=policy_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    SecurityPolicyCreated(
                        aggregate_id=str(policy.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        policy_id=str(policy.id),
                        payload={"policy_id": str(policy.id), "org_id": str(org_id)},
                    )
                )

            response = security_policy_to_response_dto(policy)
            await self.cache.set(
                security_policy_cache_key(org_id),
                response.model_dump(mode="json"),
                ttl=SECURITY_POLICY_KEY_TTL,
            )
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_default_policy failed for org {org_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Get ──────────────────────────────────────────────────────────────────

    async def get_security_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[SecurityPolicyResponseDTO]:
        """Retrieve the security policy for an organization (cache-first)."""
        try:
            SecurityPolicyPolicy.can_read(self.authorizer, ctx, org_id)

            cache_key = security_policy_cache_key(org_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(
                    data=SecurityPolicyResponseDTO(**cached),
                    metadata={"cached": True},
                )

            org_uuid = uuid.UUID(str(org_id))
            async with self.uow_service:
                repo = _SecurityPolicyRepository()
                policy = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid)],
                )

            if not policy:
                return ServiceResult.fail(
                    error=f"No security policy found for organization '{org_id}'.",
                    error_code="SECURITY_POLICY_NOT_FOUND",
                    status_code=404,
                )

            response = security_policy_to_response_dto(policy)
            await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=SECURITY_POLICY_KEY_TTL)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_security_policy failed for org {org_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Update ───────────────────────────────────────────────────────────────

    async def update_security_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: UpdateSecurityPolicyDTO,
    ) -> ServiceResult[SecurityPolicyResponseDTO]:
        """
        Apply a partial update to an org's security policy.
        Enforces platform floor constraints and publishes granular events
        for critical changes (MFA, IP restrictions, SSO).
        """
        try:
            SecurityPolicyPolicy.can_update(self.authorizer, ctx, org_id)

            # Platform floor validation
            validate_security_policy_not_looser_than_platform(dto.password_min_length)

            org_uuid = uuid.UUID(str(org_id))
            async with self.uow_service:
                repo = _SecurityPolicyRepository()
                policy = await repo.find_one(
                    session=self.uow_service.session,
                    filters=[FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_uuid)],
                )
                if not policy:
                    return ServiceResult.fail(
                        error=f"No security policy found for organization '{org_id}'.",
                        error_code="SECURITY_POLICY_NOT_FOUND",
                        status_code=404,
                    )

                update_data = dto.model_dump(exclude_unset=True)
                previous_mfa = policy.mfa_required
                previous_sso = policy.sso_enforced
                previous_ips = list(policy.allowed_ip_ranges or [])

                updated = await repo.update(
                    session=self.uow_service.session,
                    id=policy.id,
                    obj_in=update_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                changes_str = {k: str(v) for k, v in update_data.items()}

                # Always emit generic update event
                self.uow_service.add_event(
                    SecurityPolicyUpdated(
                        aggregate_id=str(policy.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        policy_id=str(policy.id),
                        changes=changes_str,
                        payload={"policy_id": str(policy.id), "changes": changes_str},
                    )
                )

                # Emit specific events for high-impact changes
                if "mfa_required" in update_data:
                    new_mfa = update_data["mfa_required"]
                    if new_mfa and not previous_mfa:
                        self.uow_service.add_event(
                            SecurityPolicyMFAEnabled(
                                aggregate_id=str(policy.id),
                                tenant_id=str(org_id),
                                actor_id=ctx.get_user_id_str(),
                                correlation_id=ctx.correlation_id,
                                policy_id=str(policy.id),
                                payload={"policy_id": str(policy.id)},
                            )
                        )
                    elif not new_mfa and previous_mfa:
                        self.uow_service.add_event(
                            SecurityPolicyMFADisabled(
                                aggregate_id=str(policy.id),
                                tenant_id=str(org_id),
                                actor_id=ctx.get_user_id_str(),
                                correlation_id=ctx.correlation_id,
                                policy_id=str(policy.id),
                                payload={"policy_id": str(policy.id)},
                            )
                        )

                if "allowed_ip_ranges" in update_data:
                    self.uow_service.add_event(
                        SecurityPolicyIPRestrictionChanged(
                            aggregate_id=str(policy.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            policy_id=str(policy.id),
                            allowed_ranges=update_data.get("allowed_ip_ranges", []),
                            payload={"policy_id": str(policy.id)},
                        )
                    )

                if update_data.get("sso_enforced") and not previous_sso:
                    self.uow_service.add_event(
                        SecurityPolicySSOEnforced(
                            aggregate_id=str(policy.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            policy_id=str(policy.id),
                            payload={"policy_id": str(policy.id)},
                        )
                    )

            # Invalidate cache — policy changes are security-critical
            await self.cache.delete(security_policy_cache_key(org_id))

            response = security_policy_to_response_dto(updated)
            return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"update_security_policy failed for org {org_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Password Validation ──────────────────────────────────────────────────

    async def validate_password_against_policy(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        password_plaintext: str,
    ) -> ServiceResult[PasswordValidationResultDTO]:
        """
        Validate a plaintext password against the organization's password policy rules.
        Used during registration, password change, and reset flows.
        """
        try:
            policy_result = await self.get_security_policy(ctx, org_id)
            if policy_result.is_failure:
                # Fall back to platform defaults if org has no policy yet
                violations = validate_password_against_policy(
                    password_plaintext=password_plaintext,
                    min_length=SECURITY_POLICY_DEFAULTS["password_min_length"],
                    require_uppercase=SECURITY_POLICY_DEFAULTS["password_require_uppercase"],
                    require_numbers=SECURITY_POLICY_DEFAULTS["password_require_numbers"],
                    require_symbols=SECURITY_POLICY_DEFAULTS["password_require_symbols"],
                )
            else:
                policy = policy_result.unwrap()
                violations = validate_password_against_policy(
                    password_plaintext=password_plaintext,
                    min_length=policy.password_min_length,
                    require_uppercase=policy.password_require_uppercase,
                    require_numbers=policy.password_require_numbers,
                    require_symbols=policy.password_require_symbols,
                )

            return ServiceResult.ok(
                data=PasswordValidationResultDTO(
                    is_valid=len(violations) == 0,
                    violations=violations,
                )
            )

        except Exception as exc:
            logger.error(f"validate_password_against_policy failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── IP Check ─────────────────────────────────────────────────────────────

    async def check_ip_allowed(
        self,
        org_id: Union[uuid.UUID, str],
        ip_address: str,
    ) -> ServiceResult[IPCheckResultDTO]:
        """
        Validate whether an IP address is within the organization's allowed IP ranges.
        Called from auth middleware — does not require ServiceContext.
        """
        try:
            # Use system context for policy lookup (no user auth required here)
            system_ctx = ServiceContext.create_system_context(organization_id=org_id)
            policy_result = await self.get_security_policy(system_ctx, org_id)
            if policy_result.is_failure:
                # No policy = unrestricted
                return ServiceResult.ok(
                    data=IPCheckResultDTO(is_allowed=True, ip_address=ip_address)
                )

            policy = policy_result.unwrap()
            if not policy.allowed_ip_ranges:
                return ServiceResult.ok(
                    data=IPCheckResultDTO(is_allowed=True, ip_address=ip_address)
                )

            try:
                request_ip = ipaddress.ip_address(ip_address)
            except ValueError:
                return ServiceResult.ok(
                    data=IPCheckResultDTO(is_allowed=False, ip_address=ip_address)
                )

            for cidr in policy.allowed_ip_ranges:
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                    if request_ip in network:
                        return ServiceResult.ok(
                            data=IPCheckResultDTO(
                                is_allowed=True,
                                matched_range=cidr,
                                ip_address=ip_address,
                            )
                        )
                except ValueError:
                    continue

            return ServiceResult.ok(
                data=IPCheckResultDTO(is_allowed=False, ip_address=ip_address)
            )

        except Exception as exc:
            logger.error(f"check_ip_allowed failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Lockout Config ───────────────────────────────────────────────────────

    async def get_lockout_config(
        self,
        org_id: Union[uuid.UUID, str],
    ) -> ServiceResult[Dict[str, int]]:
        """
        Return lockout configuration for use by the authentication layer.
        Returns max_failed_logins and lockout_duration_minutes.
        """
        try:
            system_ctx = ServiceContext.create_system_context(organization_id=org_id)
            policy_result = await self.get_security_policy(system_ctx, org_id)

            if policy_result.is_failure:
                return ServiceResult.ok(data={
                    "max_failed_logins": SECURITY_POLICY_DEFAULTS["max_failed_logins"],
                    "lockout_duration_minutes": SECURITY_POLICY_DEFAULTS["lockout_duration_minutes"],
                })

            policy = policy_result.unwrap()
            return ServiceResult.ok(data={
                "max_failed_logins": policy.max_failed_logins,
                "lockout_duration_minutes": policy.lockout_duration_minutes,
            })

        except Exception as exc:
            logger.error(f"get_lockout_config failed for org {org_id}: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
