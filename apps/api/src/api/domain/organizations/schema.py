"""
Organizations Pydantic Schemas.
"""

from pydantic import BaseModel


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
