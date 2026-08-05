from typing import Dict, List, Any
from api.ai.capabilities import BaseCapability

def allocate_budget_heuristic(
    total_budget: float,
    channel_performance: Dict[str, Dict[str, float]]
) -> List[Dict[str, Any]]:
    """
    Greedy budget optimization heuristic.
    Allocates higher percentages of budget to channels with lower cost-per-lead (CPL) / higher CTR.
    """
    if total_budget <= 0:
        return []
        
    # Heuristic metrics: calculate a priority weight based on CTR / CPC
    weights = {}
    total_weight = 0.0
    for channel, metrics in channel_performance.items():
        ctr = metrics.get("ctr", 1.0)
        cpc = metrics.get("cpc", 1.0)
        # weight is proportional to CTR and inversely proportional to CPC
        weight = ctr / cpc
        weights[channel] = weight
        total_weight += weight
        
    allocations = []
    if total_weight == 0.0:
        # Equal split
        share = 1.0 / len(channel_performance) if channel_performance else 0.0
        for channel in channel_performance:
            allocated = total_budget * share
            allocations.append({
                "channel_name": channel,
                "budget_percentage": share * 100.0,
                "allocated_amount": allocated
            })
        return allocations

    for channel, weight in weights.items():
        percentage = weight / total_weight
        allocated = total_budget * percentage
        # Estimate clicks/leads based on CPC and conversion rate (CVR)
        metrics = channel_performance[channel]
        cpc = metrics.get("cpc", 1.0)
        cvr = metrics.get("cvr", 0.02)
        
        projected_clicks = int(allocated / cpc) if cpc > 0 else 0
        projected_leads = int(projected_clicks * cvr)
        
        allocations.append({
            "channel_name": channel,
            "budget_percentage": round(percentage * 100.0, 1),
            "allocated_amount": round(allocated, 2),
            "projected_clicks": projected_clicks,
            "projected_leads": projected_leads
        })
        
    return allocations

CAMPAIGN_CAPABILITY = BaseCapability(
    name="CAMPAIGN",
    description="Enterprise Multi-channel Campaign planning, segment optimization, calendar scheduler, and creative allocation.",
    input_schema={
        "type": "object",
        "properties": {
            "total_budget": {"type": "number"},
            "channels": {"type": "array", "items": {"type": "string"}},
            "objectives": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["total_budget", "channels"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "channel_allocations": {"type": "array", "items": {"type": "object"}},
            "projected_roi": {"type": "number"}
        }
    },
    estimated_runtime=18,
    estimated_cost=0.02,
    required_tools=["knowledge_tool", "crm_tool", "email_tool", "campaign_tool", "analytics_tool"],
    required_permissions=["manage_campaign"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard multi-channel campaign directives."
)
