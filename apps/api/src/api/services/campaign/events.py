"""
EAIMOS Campaign Domain Events
===============================
Domain events for Sprint 4 Campaign & Content Management Services.
"""

from typing import Optional
from api.services.base.events import DomainEvent


class CampaignCreated(DomainEvent):
    event_type: str = "campaign.created"
    campaign_id: str = ""
    title: str = ""
    channel: str = ""


class CampaignStatusChanged(DomainEvent):
    event_type: str = "campaign.status_changed"
    campaign_id: str = ""
    old_status: str = ""
    new_status: str = ""


class CampaignScheduled(DomainEvent):
    event_type: str = "campaign.scheduled"
    campaign_id: str = ""
    scheduled_for: str = ""


class AudienceSegmentCreated(DomainEvent):
    event_type: str = "campaign.audience_segment_created"
    segment_id: str = ""
    name: str = ""


class ContentGenerated(DomainEvent):
    event_type: str = "campaign.content_generated"
    campaign_id: Optional[str] = None
    target_channel: str = ""


class VariantCreated(DomainEvent):
    event_type: str = "campaign.variant_created"
    campaign_id: str = ""
    variant_id: str = ""
    variant_name: str = ""
