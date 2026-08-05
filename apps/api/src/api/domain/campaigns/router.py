"""
Campaigns Domain Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/campaigns", tags=["Campaigns Domain"])


@router.get("/")
async def list_campaigns():
    return {"message": "Campaigns domain router scaffolded"}
