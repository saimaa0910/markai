"""
Workflow Pydantic Schemas.
"""

from pydantic import BaseModel


class WorkflowExecutionSchema(BaseModel):
    id: str
    name: str
    status: str
