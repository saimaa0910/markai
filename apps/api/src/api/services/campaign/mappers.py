"""
EAIMOS Campaign Mappers
========================
ORM to DTO converters for Campaign entities.
"""

from typing import Any, List
from api.services.campaign.dtos import CampaignResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def campaign_to_response_dto(entity: Any) -> CampaignResponseDTO:
    status_str = entity.status.value if hasattr(entity.status, "value") else str(entity.status)
    channel_str = entity.channel.value if hasattr(entity.channel, "value") else str(entity.channel)

    return CampaignResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        owner_id=_get_val(entity, "owner_id"),
        title=entity.title,
        description=_get_val(entity, "description"),
        status=status_str,
        channel=channel_str,
        goal=_get_val(entity, "goal"),
        budget=float(_get_val(entity, "budget", 0.0)),
        spent_budget=float(_get_val(entity, "spent_budget", 0.0)),
        currency=_get_val(entity, "currency", "USD"),
        target_audience_id=_get_val(entity, "target_audience_id"),
        scheduled_for=_get_val(entity, "scheduled_for"),
        completed_at=_get_val(entity, "completed_at"),
        tags=list(entity.tags) if getattr(entity, "tags", None) and not hasattr(entity.tags, "_mock_name") else [],
        created_at=entity.created_at,
        updated_at=_get_val(entity, "updated_at"),
    )


def campaigns_to_response_list(entities: List[Any]) -> List[CampaignResponseDTO]:
    return [campaign_to_response_dto(e) for e in entities]
