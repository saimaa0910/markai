"""
Billing Validators.
"""


def validate_credits_available(balance: int, cost: int) -> bool:
    return balance >= cost
