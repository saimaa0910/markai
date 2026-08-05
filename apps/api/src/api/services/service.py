"""
Base Service Orchestrator Class.
"""

from typing import Dict, Any


class BaseServiceOrchestrator:
    async def process_task(self, task_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"task": task_name, "status": "completed"}


base_service_orchestrator = BaseServiceOrchestrator()
