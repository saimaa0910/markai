"""
Integrations Model Entity.
"""

from pydantic import BaseModel


class IntegrationDomainEntity(BaseModel):
    id: str
    provider_name: str
    status: str
