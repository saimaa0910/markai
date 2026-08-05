"""
Workflow Router.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/workflow", tags=["Workflow Domain"])


@router.post("/execute")
async def run_workflow():
    return {"message": "Workflow domain router scaffolded"}
