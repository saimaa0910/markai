"""
Service Layer Business & Authorization Policies.
"""


def check_service_policy(user_role: str, required_role: str = "user") -> bool:
    return user_role == required_role or user_role == "admin"
