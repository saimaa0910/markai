"""
Users Domain Pydantic Schemas.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
