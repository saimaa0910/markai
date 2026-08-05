"""
Analytics Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics Domain"])


@router.get("/overview")
async def get_analytics_overview():
    return {"message": "Analytics domain router scaffolded"}
