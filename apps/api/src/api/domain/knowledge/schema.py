"""
Knowledge Pydantic Schemas.
"""

from pydantic import BaseModel


class DocumentResponseSchema(BaseModel):
    id: str
    title: str
