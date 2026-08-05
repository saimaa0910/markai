"""
Workflow Service.
"""

from typing import Dict, Any


class WorkflowService:
    async def trigger_execution(self, workflow_id: str) -> Dict[str, Any]:
        return {"execution_id": "exec_001"}


workflow_service = WorkflowService()
