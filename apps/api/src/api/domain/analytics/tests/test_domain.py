"""
Analytics Domain Unit Tests.
"""

from api.domain.analytics.validator import validate_metric_range


def test_metric_validation():
    assert validate_metric_range(10.0) is True
    assert validate_metric_range(-1.0) is False
