"""
Integrations Pydantic Schemas.
"""

from pydantic import BaseModel


class IntegrationResponseSchema(BaseModel):
    id: str
    provider_name: str
    status: str
