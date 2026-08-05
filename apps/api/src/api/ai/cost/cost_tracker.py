"""
Token Consumption & Model Pricing Cost Tracker.
"""

from typing import Dict, Any
from pydantic import BaseModel


class TokenUsageRecord(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class CostTracker:
    """
    Tracks and records LLM API expenditure per organization.
    """
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"prompt": 0.000005, "completion": 0.000015},
        "claude-3-5-sonnet": {"prompt": 0.000003, "completion": 0.000015},
    }

    def record_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> TokenUsageRecord:
        """
        Calculate cost and generate token usage record.
        """
        pricing = self.MODEL_PRICING.get(model, {"prompt": 0.000002, "completion": 0.000006})
        cost = (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])
        return TokenUsageRecord(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=cost,
        )


cost_tracker = CostTracker()
