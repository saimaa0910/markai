"""
Auth Domain Input Validation Helpers.
"""


def validate_password_strength(password: str) -> bool:
    """
    Validate password complexity rules.
    """
    return len(password) >= 8
