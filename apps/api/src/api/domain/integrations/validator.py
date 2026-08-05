"""
Integrations Validators.
"""


def validate_provider_name(provider: str) -> bool:
    return len(provider.strip()) > 0
