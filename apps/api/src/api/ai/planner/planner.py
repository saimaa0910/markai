"""
Multi-Step Goal Decomposition & Reasoning Planner
==================================================
Wires the ai/planner stub to the production AgentPlannerService.
No duplication — delegates entirely to services/agent_planner.py.
"""
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session


class ExecutionStep(BaseModel):
    step_number: int
    action: str
    tool_name: Optional[str] = None
    input_params: Dict[str, Any] = {}


class ExecutionPlan(BaseModel):
    plan_id: str
    goal: str
    thought: str
    steps: List[ExecutionStep]


class AIPlanner:
    """
    Goal Decomposition & Step Planner.
    Delegates to AgentPlannerService — no logic duplication.
    """

    def create_plan(
        self,
        db: Session,
        agent: Any,
        user_input: str,
        session_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Decompose user goal into sequential execution steps via LLM.
        Returns raw plan dict: {"thought": str, "steps": [...]}.
        """
        from api.services.agent_planner import AgentPlannerService
        return AgentPlannerService.generate_plan(
            db=db,
            agent=agent,
            user_input=user_input,
            session_id=session_id,
            organization_id=organization_id,
            user_id=user_id,
        )

    def to_execution_plan(self, plan_dict: Dict[str, Any], goal: str) -> ExecutionPlan:
        """Convert raw plan dict to typed ExecutionPlan."""
        steps = []
        for i, step in enumerate(plan_dict.get("steps", []), start=1):
            steps.append(ExecutionStep(
                step_number=i,
                action=step.get("description", step.get("tool_name", "step")),
                tool_name=step.get("tool_name"),
                input_params=step.get("tool_params", {}),
            ))
        return ExecutionPlan(
            plan_id=f"plan_{id(plan_dict)}",
            goal=goal,
            thought=plan_dict.get("thought", ""),
            steps=steps,
        )


ai_planner = AIPlanner()
