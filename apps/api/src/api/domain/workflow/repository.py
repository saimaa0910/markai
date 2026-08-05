"""
Workflow Repository.
"""

from typing import Optional, Any


class WorkflowRepository:
    async def get_by_id(self, workflow_id: str) -> Optional[Any]:
        return None


workflow_repository = WorkflowRepository()
