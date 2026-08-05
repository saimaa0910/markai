"""
Organizations Validators.
"""


def validate_org_slug(slug: str) -> bool:
    return slug.islower() and slug.isalnum()
