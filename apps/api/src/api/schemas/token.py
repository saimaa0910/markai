from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    mfa_required: Optional[bool] = None
    mfa_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Body contract for token refresh (P2-11): token travels in the body, not the URL."""
    refresh_token: str = Field(..., min_length=1, description="The refresh token to rotate.")


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
