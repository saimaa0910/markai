"""
Users Domain FastAPI Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users Domain"])


@router.get("/me")
async def get_current_user():
    """
    Get authenticated user profile.
    """
    return {"message": "Users domain router scaffolded"}
