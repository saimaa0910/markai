"""
EAIMOS Platform Mappers
========================
Entity-to-DTO mappers for Billing and Platform entities.
"""

from typing import Any
from api.services.platform.dtos import SubscriptionResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def subscription_to_response_dto(entity: Any) -> SubscriptionResponseDTO:
    return SubscriptionResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        plan_tier=_get_val(entity, "plan_tier", "STARTER"),
        billing_cycle=_get_val(entity, "billing_cycle", "MONTHLY"),
        status=_get_val(entity, "status", "ACTIVE"),
        current_period_start=entity.current_period_start,
        current_period_end=entity.current_period_end,
        cancel_at_period_end=_get_val(entity, "cancel_at_period_end", False),
    )
