"""
Billing Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/billing", tags=["Billing Domain"])


@router.get("/subscription")
async def get_sub():
    return {"message": "Billing domain router scaffolded"}
