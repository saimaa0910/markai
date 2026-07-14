import uuid
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from api.models.ai_usage import AITokenUsage
from api.models.campaign import Campaign, CampaignAnalytics
from api.models.lead import Lead


class AnalyticsService:
    """
    Business intelligence service for generating executive aggregation reports.
    Aggregates token costs, marketing pipelines, and campaign ROI.
    """

    @staticmethod
    def get_executive_summary(
        db: Session,
        organization_id: uuid.UUID,
    ) -> Dict[str, Any]:
        # 1. Total Token Usage metrics
        usage_stmt = select(
            func.sum(AITokenUsage.total_tokens).label("total_tokens"),
            func.sum(AITokenUsage.cost_usd).label("total_cost"),
            func.avg(AITokenUsage.latency_ms).label("avg_latency"),
        ).where(
            and_(
                AITokenUsage.organization_id == organization_id,
                AITokenUsage.deleted_at.is_(None),
            )
        )
        usage_res = db.execute(usage_stmt).first()
        token_count = usage_res.total_tokens if usage_res and usage_res.total_tokens else 0
        total_cost = float(usage_res.total_cost) if usage_res and usage_res.total_cost else 0.0
        avg_latency = float(usage_res.avg_latency) if usage_res and usage_res.avg_latency else 0.0

        # 2. Total campaign revenues
        revenue_stmt = select(
            func.sum(CampaignAnalytics.revenue).label("total_revenue")
        ).where(
            and_(
                CampaignAnalytics.organization_id == organization_id,
                CampaignAnalytics.deleted_at.is_(None),
            )
        )
        rev_res = db.execute(revenue_stmt).first()
        total_revenue = float(rev_res.total_revenue) if rev_res and rev_res.total_revenue else 0.0

        # 3. CRM Lead summary count & value
        lead_stmt = select(
            func.count(Lead.id).label("lead_count"),
            func.sum(Lead.value).label("total_value"),
        ).where(
            and_(
                Lead.organization_id == organization_id,
                Lead.deleted_at.is_(None),
            )
        )
        lead_res = db.execute(lead_stmt).first()
        lead_count = lead_res.lead_count if lead_res and lead_res.lead_count else 0
        lead_value = float(lead_res.total_value) if lead_res and lead_res.total_value else 0.0

        return {
            "ai_platform": {
                "total_tokens_used": token_count,
                "total_gateway_cost_usd": round(total_cost, 4),
                "average_latency_ms": round(avg_latency, 2),
            },
            "campaigns": {
                "total_revenue_usd": round(total_revenue, 2),
            },
            "crm": {
                "total_leads": lead_count,
                "pipeline_value_usd": round(lead_value, 2),
            },
            "roi_ratio": (
                round(total_revenue / total_cost, 2)
                if total_cost > 0
                else 0.0
            ),
        }

    @staticmethod
    def get_token_usage_trends(
        db: Session,
        organization_id: uuid.UUID,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Return daily aggregated token count and cost records."""
        start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        
        if db.bind.dialect.name == "sqlite":
            day_field = func.date(AITokenUsage.created_at).label("day")
        else:
            day_field = func.date_trunc("day", AITokenUsage.created_at).label("day")

        stmt = (
            select(
                day_field,
                func.sum(AITokenUsage.total_tokens).label("tokens"),
                func.sum(AITokenUsage.cost_usd).label("cost"),
            )
            .where(
                and_(
                    AITokenUsage.organization_id == organization_id,
                    AITokenUsage.created_at >= start_date,
                    AITokenUsage.deleted_at.is_(None),
                )
            )
            .group_by("day")
            .order_by("day")
        )
        res = db.execute(stmt).all()

        trends = []
        for r in res:
            date_val = r.day
            if hasattr(date_val, "date") and callable(getattr(date_val, "date")):
                date_str = date_val.date().isoformat()
            elif hasattr(date_val, "isoformat") and callable(getattr(date_val, "isoformat")):
                date_str = date_val.isoformat()
            else:
                date_str = str(date_val)

            trends.append({
                "date": date_str,
                "tokens_used": r.tokens or 0,
                "cost_usd": float(r.cost or 0.0),
            })
        return trends
