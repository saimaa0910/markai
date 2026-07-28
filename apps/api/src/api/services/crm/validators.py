"""
EAIMOS CRM Validators
======================
Validation for deal amounts, probability, and statuses.
"""

from api.services.base.service_exceptions import ValidationError
from api.services.crm.constants import SUPPORTED_DEAL_STATUSES, SUPPORTED_LEAD_STATUSES


def validate_deal_status_supported(status: str) -> None:
    if status.upper() not in SUPPORTED_DEAL_STATUSES:
        raise ValidationError(
            message=f"Unsupported deal status '{status}'.",
            field_errors=[{"field": "status", "message": f"Supported statuses: {sorted(SUPPORTED_DEAL_STATUSES)}"}],
        )


def validate_lead_status_supported(status: str) -> None:
    if status.upper() not in SUPPORTED_LEAD_STATUSES:
        raise ValidationError(
            message=f"Unsupported lead status '{status}'.",
            field_errors=[{"field": "status", "message": f"Supported lead statuses: {sorted(SUPPORTED_LEAD_STATUSES)}"}],
        )
