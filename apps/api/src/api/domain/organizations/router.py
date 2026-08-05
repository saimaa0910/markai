"""
Organizations Domain FastAPI Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["Organizations Domain"])


@router.get("/")
async def list_organizations():
    return {"message": "Organizations domain router scaffolded"}
