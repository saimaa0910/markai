"""
CRM Model Entity.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class ContactEntity(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
