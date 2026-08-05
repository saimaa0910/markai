"""
Integrations Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/integrations", tags=["Integrations Domain"])


@router.get("/")
async def list_active_integrations():
    return {"message": "Integrations domain router scaffolded"}
