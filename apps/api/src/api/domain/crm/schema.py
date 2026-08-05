"""
CRM Pydantic Schemas.
"""

from pydantic import BaseModel, EmailStr


class ContactResponseSchema(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
