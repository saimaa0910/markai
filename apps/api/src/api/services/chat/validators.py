"""
EAIMOS Chat Validators
=======================
Validation for temperatures, roles, and message content.
"""

from api.services.base.service_exceptions import ValidationError
from api.services.chat.constants import SUPPORTED_CHAT_ROLES


def validate_chat_role_supported(role: str) -> None:
    if role.upper() not in SUPPORTED_CHAT_ROLES:
        raise ValidationError(
            message=f"Unsupported chat role '{role}'.",
            field_errors=[{"field": "role", "message": f"Supported roles: {sorted(SUPPORTED_CHAT_ROLES)}"}],
        )
