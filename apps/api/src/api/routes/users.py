from typing import Any
from fastapi import APIRouter, Depends
from api.core.deps import get_current_user
from api.models.user import User
from api.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get profile details of the currently authenticated user.
    """
    return current_user
