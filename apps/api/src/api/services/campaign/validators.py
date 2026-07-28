"""
EAIMOS Campaign Validators
===========================
Validation functions for Campaign scheduling, budgets, and channels.
"""

from datetime import datetime, timezone
from api.services.base.service_exceptions import ValidationError, BusinessRuleViolation
from api.services.campaign.constants import SUPPORTED_CAMPAIGN_CHANNELS, SUPPORTED_CAMPAIGN_STATUSES


def validate_channel_supported(channel: str) -> None:
    if channel.upper() not in SUPPORTED_CAMPAIGN_CHANNELS:
        raise ValidationError(
            message=f"Unsupported campaign channel '{channel}'.",
            field_errors=[{"field": "channel", "message": f"Supported channels: {sorted(SUPPORTED_CAMPAIGN_CHANNELS)}"}],
        )


def validate_campaign_status_supported(status: str) -> None:
    if status.upper() not in SUPPORTED_CAMPAIGN_STATUSES:
        raise ValidationError(
            message=f"Unsupported campaign status '{status}'.",
            field_errors=[{"field": "status", "message": f"Supported statuses: {sorted(SUPPORTED_CAMPAIGN_STATUSES)}"}],
        )


def validate_schedule_time_future(scheduled_for: datetime) -> None:
    now = datetime.now(timezone.utc)
    if scheduled_for.tzinfo is None:
        scheduled_for = scheduled_for.replace(tzinfo=timezone.utc)
    if scheduled_for <= now:
        raise BusinessRuleViolation(
            message="Campaign scheduled time must be in the future.",
            rule_name="INVALID_SCHEDULE_TIME",
        )
