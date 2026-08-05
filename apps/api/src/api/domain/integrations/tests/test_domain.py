"""
Integrations Domain Unit Tests.
"""

from api.domain.integrations.validator import validate_provider_name


def test_provider_validation():
    assert validate_provider_name("google") is True
    assert validate_provider_name("   ") is False
