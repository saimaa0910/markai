from typing import Dict, Any, List

def reflect_on_campaign(
    total_budget: float,
    allocations: List[Dict[str, Any]],
    calendar_events_count: int
) -> Dict[str, Any]:
    """Verify that spend limits are respected and calendar items are scheduled."""
    warnings = []
    
    # 1. Budget reconciliation check
    allocated_sum = sum(item.get("allocated_amount", 0.0) for item in allocations)
    if abs(allocated_sum - total_budget) > 1.0:
        warnings.append(f"Budget reconciliation error: Total budget is {total_budget}, but allocations sum up to {allocated_sum:.2f}.")
        
    # 2. Heuristic allocations check
    for item in allocations:
        pct = item.get("budget_percentage", 0.0)
        if pct <= 0.0 or pct > 100.0:
            warnings.append(f"Invalid allocation percentage for channel '{item.get('channel_name')}': {pct}%.")
            
    # 3. Calendar checkpoints
    if calendar_events_count < len(allocations):
        warnings.append(f"Sparse calendar warning: Only {calendar_events_count} launch checkpoints are scheduled for {len(allocations)} active channels.")
        
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "Campaign constraints comply successfully."
    }
