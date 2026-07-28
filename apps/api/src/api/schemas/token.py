from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    mfa_required: Optional[bool] = None
    mfa_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
