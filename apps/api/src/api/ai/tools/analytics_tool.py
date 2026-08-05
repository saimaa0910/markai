"""
Analytics Tool — Query Agent & Campaign Metrics
================================================
Delegates to existing AnalyticsService / AgentRun data.
Allows agents to self-report performance or query campaign metrics.
"""
import uuid
from typing import Dict, Any
from api.ai.tools import BaseTool, ToolInput, ToolResult


class AnalyticsTool(BaseTool):

    @property
    def name(self) -> str:
        return "analytics_tool"

    @property
    def description(self) -> str:
        return (
            "Query analytics data for agent runs, campaigns, or organization metrics. "
            "Returns token usage, cost, success rates, and run statistics."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metric_type": {
                    "type": "string",
                    "enum": ["agent_runs", "campaign_stats", "token_usage", "cost_summary"],
                    "description": "Type of analytics metric to retrieve",
                },
                "agent_id": {
                    "type": "string",
                    "description": "Optional agent UUID to scope metrics",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Number of records to return",
                },
            },
            "required": ["metric_type"],
        }

    def execute(self, input: ToolInput, db: Any) -> ToolResult:
        metric_type = input.params.get("metric_type", "")
        agent_id_str = input.params.get("agent_id")
        limit = int(input.params.get("limit", 10))
        org_id = uuid.UUID(input.organization_id)

        try:
            if metric_type == "agent_runs":
                return self._get_agent_runs(db, org_id, agent_id_str, limit)
            elif metric_type == "token_usage":
                return self._get_token_usage(db, org_id, limit)
            elif metric_type == "cost_summary":
                return self._get_cost_summary(db, org_id)
            elif metric_type == "campaign_stats":
                return self._get_campaign_stats(db, org_id, limit)
            else:
                return ToolResult(success=False, tool_name=self.name, error=f"Unknown metric_type: {metric_type}")
        except Exception as e:
            return ToolResult(success=False, tool_name=self.name, error=f"Analytics query failed: {str(e)}")

    def _get_agent_runs(self, db: Any, org_id: uuid.UUID, agent_id_str: Any, limit: int) -> ToolResult:
        from api.models.agent import AgentRun, AgentSession
        from sqlalchemy import select

        query = select(AgentRun).join(AgentSession).where(
            AgentSession.organization_id == org_id,
            AgentRun.deleted_at.is_(None),
        )
        if agent_id_str:
            try:
                query = query.where(AgentSession.agent_id == uuid.UUID(agent_id_str))
            except ValueError:
                pass

        runs = db.scalars(query.limit(limit)).all()
        total = len(runs)
        completed = sum(1 for r in runs if r.status.value == "COMPLETED")

        return ToolResult(
            success=True,
            tool_name=self.name,
            output={
                "total_runs": total,
                "completed": completed,
                "failed": total - completed,
                "success_rate": round(completed / total * 100, 2) if total > 0 else 100.0,
                "total_tokens": sum(r.total_tokens for r in runs),
                "avg_latency_ms": round(
                    sum(r.latency_ms for r in runs if r.latency_ms) / max(1, sum(1 for r in runs if r.latency_ms)),
                    2,
                ),
            },
        )

    def _get_token_usage(self, db: Any, org_id: uuid.UUID, limit: int) -> ToolResult:
        from api.models.ai_platform import AIUsage
        from sqlalchemy import select

        records = db.scalars(
            select(AIUsage)
            .where(AIUsage.organization_id == org_id)
            .order_by(AIUsage.created_at.desc())
            .limit(limit)
        ).all()

        return ToolResult(
            success=True,
            tool_name=self.name,
            output={
                "records": [
                    {
                        "provider": r.provider,
                        "model": r.model,
                        "prompt_tokens": r.prompt_tokens,
                        "completion_tokens": r.completion_tokens,
                        "total_tokens": r.total_tokens,
                        "cost_usd": float(r.cost_usd),
                    }
                    for r in records
                ],
                "total_records": len(records),
            },
        )

    def _get_cost_summary(self, db: Any, org_id: uuid.UUID) -> ToolResult:
        from api.models.ai_platform import AICost
        from sqlalchemy import select, func

        result = db.execute(
            select(
                func.sum(AICost.cost_usd).label("total_cost"),
                func.sum(AICost.input_tokens).label("total_input"),
                func.sum(AICost.output_tokens).label("total_output"),
                func.count(AICost.id).label("total_calls"),
            ).where(AICost.organization_id == org_id)
        ).first()

        return ToolResult(
            success=True,
            tool_name=self.name,
            output={
                "total_cost_usd": round(float(result.total_cost or 0), 6),
                "total_input_tokens": int(result.total_input or 0),
                "total_output_tokens": int(result.total_output or 0),
                "total_api_calls": int(result.total_calls or 0),
            },
        )

    def _get_campaign_stats(self, db: Any, org_id: uuid.UUID, limit: int) -> ToolResult:
        from api.models.campaign import Campaign
        from sqlalchemy import select

        campaigns = db.scalars(
            select(Campaign)
            .where(Campaign.organization_id == org_id, Campaign.deleted_at.is_(None))
            .limit(limit)
        ).all()

        return ToolResult(
            success=True,
            tool_name=self.name,
            output={
                "campaigns": [
                    {"id": str(c.id), "name": c.name, "status": c.status.value if hasattr(c.status, "value") else str(c.status)}
                    for c in campaigns
                ],
                "total": len(campaigns),
            },
        )
