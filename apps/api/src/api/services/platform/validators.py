"""
EAIMOS Platform Validators
===========================
Validation for plan tiers, credit amounts, and threat severities.
"""

from api.services.base.service_exceptions import ValidationError, BusinessRuleViolation
from api.services.platform.constants import SUPPORTED_PLAN_TIERS, SUPPORTED_THREAT_SEVERITIES


def validate_plan_tier_supported(plan_tier: str) -> None:
    if plan_tier.upper() not in SUPPORTED_PLAN_TIERS:
        raise ValidationError(
            message=f"Unsupported plan tier '{plan_tier}'.",
            field_errors=[{"field": "plan_tier", "message": f"Supported tiers: {sorted(SUPPORTED_PLAN_TIERS)}"}],
        )


def validate_threat_severity_supported(severity: str) -> None:
    if severity.upper() not in SUPPORTED_THREAT_SEVERITIES:
        raise ValidationError(
            message=f"Unsupported threat severity '{severity}'.",
            field_errors=[{"field": "severity", "message": f"Supported severities: {sorted(SUPPORTED_THREAT_SEVERITIES)}"}],
        )
