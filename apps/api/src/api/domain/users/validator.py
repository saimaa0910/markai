"""
Users Domain Input Validation Helpers.
"""


def validate_username_format(username: str) -> bool:
    return len(username) >= 3 and username.isalnum()
