"""
Auth Domain Entity Model.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
