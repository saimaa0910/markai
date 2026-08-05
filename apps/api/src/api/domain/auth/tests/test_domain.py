"""
Auth Domain Unit Tests.
"""

from api.domain.auth.validator import validate_password_strength


def test_password_validation():
    assert validate_password_strength("securepass123") is True
    assert validate_password_strength("short") is False
