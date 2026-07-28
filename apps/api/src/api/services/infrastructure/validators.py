"""
EAIMOS Infrastructure Validators
=================================
Validation rules for file storage, notification channels, and feature flags.
"""

from api.services.base.service_exceptions import ValidationError
from api.services.infrastructure.constants import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_NOTIFICATION_TYPES,
)


def validate_file_size(file_size: int) -> None:
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            message=f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES} bytes.",
            field_errors=[{"field": "file_size", "message": f"Size {file_size} exceeds {MAX_FILE_SIZE_BYTES}"}],
        )


def validate_notification_channel(channel: str) -> None:
    if channel.upper() not in SUPPORTED_NOTIFICATION_TYPES:
        raise ValidationError(
            message=f"Unsupported notification channel '{channel}'.",
            field_errors=[{"field": "channel", "message": f"Supported channels: {sorted(SUPPORTED_NOTIFICATION_TYPES)}"}],
        )
