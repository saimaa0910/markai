"""
EAIMOS Observability Validators
================================
Validation for log levels and alert severities.
"""

from api.services.base.service_exceptions import ValidationError
from api.services.observability.constants import SUPPORTED_ALERT_SEVERITIES, SUPPORTED_LOG_LEVELS


def validate_log_level_supported(level: str) -> None:
    if level.upper() not in SUPPORTED_LOG_LEVELS:
        raise ValidationError(
            message=f"Unsupported log level '{level}'.",
            field_errors=[{"field": "level", "message": f"Supported levels: {sorted(SUPPORTED_LOG_LEVELS)}"}],
        )


def validate_alert_severity_supported(severity: str) -> None:
    if severity.upper() not in SUPPORTED_ALERT_SEVERITIES:
        raise ValidationError(
            message=f"Unsupported alert severity '{severity}'.",
            field_errors=[{"field": "severity", "message": f"Supported severities: {sorted(SUPPORTED_ALERT_SEVERITIES)}"}],
        )
