"""
Notifications Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications Domain"])


@router.post("/send")
async def send_notif():
    return {"message": "Notifications domain router scaffolded"}
