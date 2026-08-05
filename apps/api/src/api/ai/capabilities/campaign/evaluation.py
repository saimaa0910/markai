from typing import Dict, Any, List

def evaluate_campaign(
    total_budget: float,
    allocations: List[Dict[str, Any]],
    projected_roi: float
) -> Dict[str, Any]:
    """Grade campaign budget dispatching efficiency and ROI estimation."""
    # 1. Budget reconciliation score (Max 40 points)
    allocated_sum = sum(item.get("allocated_amount", 0.0) for item in allocations)
    diff = abs(allocated_sum - total_budget)
    reconcile_score = max(0.0, 40.0 - (diff * 2.0))
    
    # 2. Channel diversification (Max 30 points)
    # Penalize campaign plans putting 100% budget in a single channel
    pcts = [item.get("budget_percentage", 0.0) for item in allocations]
    max_pct = max(pcts) if pcts else 100.0
    diversify_score = max(0.0, 30.0 - ((max_pct - 50.0) * 0.6) if max_pct > 50.0 else 30.0)
    
    # 3. Projected ROI reliability (Max 30 points)
    # Standard benchmark: expected ROI for SaaS launch is between 50% and 300%
    roi_score = 30.0
    if projected_roi < 20.0 or projected_roi > 400.0:
        roi_score = 15.0
        
    total_score = reconcile_score + diversify_score + roi_score
    
    return {
        "score": round(total_score, 1),
        "metrics": {
            "budget_reconciliation": round(reconcile_score / 40.0 * 100.0, 1) if reconcile_score > 0 else 0.0,
            "channel_diversification": round(diversify_score / 30.0 * 100.0, 1) if diversify_score > 0 else 0.0,
            "roi_projected_reliability": round(roi_score / 30.0 * 100.0, 1) if roi_score > 0 else 0.0
        }
    }
