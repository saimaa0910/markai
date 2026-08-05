"""
Notifications Validators.
"""


def validate_notification_content(title: str, msg: str) -> bool:
    return len(title) > 0 and len(msg) > 0
