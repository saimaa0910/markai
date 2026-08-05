"""
Social Agent Validators — Sprint 7.5
=======================================
Input validation for social generation, scheduling, and publishing requests.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException
from api.ai.agents.social.constants import SocialPlatform, PLATFORM_CONFIGS


def validate_social_input(
    prompt: str,
    platform: Optional[SocialPlatform] = None,
    keywords: Optional[List[str]] = None,
) -> None:
    """Validate core social generation inputs."""
    clean = prompt.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Social prompt cannot be empty.")
    if len(clean) < 10:
        raise HTTPException(
            status_code=400,
            detail="Social prompt is too short. Provide at least 10 characters.",
        )
    if len(clean) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Social prompt exceeds maximum allowed length of 5000 characters.",
        )
    if keywords:
        for kw in keywords:
            if not kw.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Keywords list contains empty entries.",
                )
            if len(kw) > 100:
                raise HTTPException(
                    status_code=400,
                    detail=f"Keyword '{kw[:30]}...' exceeds maximum length of 100 characters.",
                )


def validate_schedule_input(
    scheduled_at: Optional[datetime] = None,
    timezone: Optional[str] = None,
    recurring_pattern: Optional[str] = None,
) -> None:
    """Validate scheduling inputs."""
    if scheduled_at:
        now = datetime.now(tz=timezone.utc if not scheduled_at.tzinfo else scheduled_at.tzinfo)
        if scheduled_at < now:
            raise HTTPException(
                status_code=400,
                detail="Scheduled time cannot be in the past.",
            )

    valid_timezones = [
        "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
        "Europe/London", "Europe/Paris", "Asia/Kolkata", "Asia/Tokyo",
        "Australia/Sydney", "America/Sao_Paulo",
    ]
    if timezone and timezone not in valid_timezones:
        # Don't hard fail — just warn via pass (real impl would use pytz)
        pass

    if recurring_pattern:
        valid_patterns = [
            "every_monday_9am", "every_tuesday_9am", "every_wednesday_9am",
            "every_thursday_9am", "every_friday_9am", "every_saturday_9am",
            "every_sunday_9am", "daily_9am", "weekly", "biweekly", "monthly",
        ]
        if recurring_pattern not in valid_patterns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recurring pattern '{recurring_pattern}'. "
                       f"Valid: {', '.join(valid_patterns)}",
            )


def validate_platform_content(content: str, platform: str) -> None:
    """Validate content against platform character limits."""
    cfg = PLATFORM_CONFIGS.get(platform.upper(), {})
    char_limit = cfg.get("char_limit", 2200)
    if len(content) > char_limit:
        raise HTTPException(
            status_code=422,
            detail=f"Content length {len(content)} exceeds {platform} limit of {char_limit} characters.",
        )


def validate_publish_request(
    platform: str,
    content: str,
    image_url: Optional[str] = None,
) -> None:
    """Validate a publish request before dispatching to platform adapters."""
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Cannot publish an empty post.")
    validate_platform_content(content, platform)
    cfg = PLATFORM_CONFIGS.get(platform.upper(), {})
    if not cfg.get("supports_images", True) and image_url:
        raise HTTPException(
            status_code=422,
            detail=f"Platform {platform} does not support image attachments.",
        )
