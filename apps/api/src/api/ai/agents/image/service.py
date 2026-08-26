import json
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Generator
from sqlalchemy.orm import Session

from api.models.agent import AgentSession, AgentRun, AgentRunStatus
from api.ai.agents.image.planner import ImagePlanner
from api.ai.agents.image.executor import ImageExecutor

logger = logging.getLogger(__name__)


def _sse(event: str, data: Any) -> str:
    """Format SSE payload message."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


class ImageAgentService:
    """
    Service Orchestration layer for the Flagship Image Generation Agent.
    Implements sync operations and Server-Sent Events (SSE) streaming workflows.
    """

    @staticmethod
    def generate_sync(
        db: Session,
        session: AgentSession,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        campaign_id: Optional[uuid.UUID] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Runs the complete layout pipeline synchronously."""
        executor = ImageExecutor(db, session.organization_id, session.user_id)
        return executor.generate(
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            campaign_id=campaign_id,
            knowledge_collections=knowledge_collections,
            model=model,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale
        )

    @staticmethod
    def generate_stream(
        db: Session,
        session: AgentSession,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        campaign_id: Optional[uuid.UUID] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
    ) -> Generator[str, None, None]:
        """
        Executes layout pipeline yielding real-time SSE stream events
        for canvas timelines and loading animations.
        """
        run_id = uuid.uuid4()
        
        yield _sse("agent_start", {
            "run_id": str(run_id),
            "agent_id": str(session.agent_id),
            "session_id": str(session.id),
        })

        try:
            # 1. Planning Step
            yield _sse("status", {"message": "Drafting layout composition plan..."})
            time.sleep(0.2)
            plan = ImagePlanner.generate_plan(
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                campaign_id=str(campaign_id) if campaign_id else None,
                has_collections=bool(knowledge_collections)
            )
            yield _sse("plan", plan)

            # 2. Execution Step
            yield _sse("status", {"message": "Applying brand voice and styles..."})
            time.sleep(0.2)
            
            yield _sse("status", {"message": "Executing image generation with priority provider..."})
            executor = ImageExecutor(db, session.organization_id, session.user_id)
            res = executor.generate(
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                campaign_id=campaign_id,
                knowledge_collections=knowledge_collections,
                model=model,
                seed=seed,
                steps=steps,
                cfg_scale=cfg_scale
            )
            
            # Emit token/progress status
            yield _sse("status", {"message": "Visual layout rendered successfully."})
            
            # 3. Reflection
            yield _sse("status", {"message": "Running visual composition reflection pass..."})
            yield _sse("reflection", res["reflection"])

            # 4. Evaluation
            yield _sse("status", {"message": "Grading creative layout metrics..."})
            yield _sse("evaluation", res["evaluation"])

            # 5. Done
            yield _sse("done", res)

        except Exception as e:
            logger.error("Streaming image generation failed: %s", e)
            yield _sse("error", {
                "message": str(e),
                "code": "GENERATION_FAILED",
                "details": {"mode": "stream"},
            })
