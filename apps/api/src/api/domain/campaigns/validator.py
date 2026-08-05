"""
Campaigns Validators.
"""


def validate_budget_amount(budget: float) -> bool:
    return budget >= 0
