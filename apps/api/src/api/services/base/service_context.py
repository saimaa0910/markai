"""
EAIMOS Service Context Module
=============================
Encapsulates execution context, user identity, tenant boundaries, authorization context,
correlation/tracing metadata, and feature flags across the Service Layer.
Framework-independent and strict typing compliant.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
import uuid


@dataclass(frozen=True)
class ServiceContext:
    """
    Immutable execution context passed through service calls.
    Carries identity, multi-tenant organization boundary, permissions, and request metadata.
    """

    user_id: Optional[Union[uuid.UUID, str]] = None
    organization_id: Optional[Union[uuid.UUID, str]] = None
    roles: List[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    is_super_admin: bool = False
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_user_id_uuid(self) -> Optional[uuid.UUID]:
        """Return user_id as a UUID object if available."""
        if not self.user_id:
            return None
        if isinstance(self.user_id, uuid.UUID):
            return self.user_id
        try:
            return uuid.UUID(str(self.user_id))
        except (ValueError, TypeError):
            return None

    def get_user_id_str(self) -> Optional[str]:
        """Return string representation of user_id if present."""
        return str(self.user_id) if self.user_id is not None else None

    def get_org_id_str(self) -> Optional[str]:
        """Return string representation of organization_id if present."""
        return str(self.organization_id) if self.organization_id is not None else None

    def get_org_id_uuid(self) -> Optional[uuid.UUID]:
        """Return organization_id as a UUID object if available."""
        if not self.organization_id:
            return None
        if isinstance(self.organization_id, uuid.UUID):
            return self.organization_id
        try:
            return uuid.UUID(str(self.organization_id))
        except (ValueError, TypeError):
            return None

    def has_permission(self, permission: str) -> bool:
        """Check if context contains specified permission or if super admin."""
        if self.is_super_admin:
            return True
        return permission in self.permissions or "*:*" in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if context contains specified role or if super admin."""
        if self.is_super_admin:
            return True
        return role in self.roles or "super_admin" in self.roles

    def has_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Check status of a feature flag in context."""
        return self.feature_flags.get(flag_name, default)

    def is_tenant_member(self, target_org_id: Union[uuid.UUID, str]) -> bool:
        """Check if context matches target tenant/organization ID."""
        if self.is_super_admin:
            return True
        if not self.organization_id:
            return False
        return str(self.organization_id) == str(target_org_id)

    def with_correlation_id(self, new_correlation_id: str) -> "ServiceContext":
        """Return a new ServiceContext instance with updated correlation_id."""
        return ServiceContext(
            user_id=self.user_id,
            organization_id=self.organization_id,
            roles=list(self.roles),
            permissions=set(self.permissions),
            correlation_id=new_correlation_id,
            trace_id=self.trace_id,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            is_super_admin=self.is_super_admin,
            feature_flags=dict(self.feature_flags),
            metadata=dict(self.metadata),
        )

    @classmethod
    def create_system_context(
        cls,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> "ServiceContext":
        """Factory method creating system/background execution context with elevated privileges."""
        return cls(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=organization_id,
            roles=["system_admin", "super_admin"],
            permissions={"*:*"},
            correlation_id=correlation_id or str(uuid.uuid4()),
            is_super_admin=True,
            metadata={"system_generated": True},
        )
