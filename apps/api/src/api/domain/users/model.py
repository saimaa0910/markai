"""
Users Domain Entity Model.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserDomainEntity(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
