"""
CRM Validators.
"""


def validate_email_domain(email: str) -> bool:
    return "@" in email
