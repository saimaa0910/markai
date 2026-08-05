"""
Auth Domain FastAPI Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth Domain"])


@router.post("/login")
async def login():
    """
    User authentication endpoint.
    """
    return {"message": "Auth endpoint scaffolded"}
