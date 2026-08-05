"""
Users Domain Unit Tests.
"""

from api.domain.users.validator import validate_username_format


def test_username_validation():
    assert validate_username_format("john123") is True
    assert validate_username_format("ab") is False
