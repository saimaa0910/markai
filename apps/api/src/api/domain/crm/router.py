"""
CRM Domain Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/crm", tags=["CRM Domain"])


@router.get("/contacts")
async def list_contacts():
    return {"message": "CRM domain router scaffolded"}
