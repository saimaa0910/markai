"""
Knowledge Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["Knowledge Domain"])


@router.get("/documents")
async def get_documents():
    return {"message": "Knowledge domain router scaffolded"}
