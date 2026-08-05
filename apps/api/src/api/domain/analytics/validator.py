"""
Analytics Validators.
"""


def validate_metric_range(val: float, min_v: float = 0.0) -> bool:
    return val >= min_v
