"""
Organizations Model Entity.
"""

from pydantic import BaseModel


class OrganizationDomainEntity(BaseModel):
    id: str
    name: str
    slug: str
