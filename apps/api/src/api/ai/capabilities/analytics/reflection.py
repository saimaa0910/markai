from typing import Dict, Any, List
from api.ai.capabilities.analytics.helpers import calculate_ltv_cac_ratio

def reflect_on_analytics(
    arpu: float,
    churn_rate: float,
    cac: float,
    anomalies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Verify that arithmetic metrics are sound and alert values are rational."""
    warnings = []
    
    # 1. Churn sanity
    if churn_rate < 0.0 or churn_rate > 1.0:
        warnings.append(f"Invalid churn rate parameter: {churn_rate}. Must be between 0.0 and 1.0 (e.g. 0.05 for 5%).")
        
    # 2. Ratio sanity
    ratio = calculate_ltv_cac_ratio(arpu, churn_rate, cac)
    if ratio > 0.0 and ratio < 1.0:
        warnings.append(f"Caution: Unit economics are unsustainable. LTV/CAC ratio is {ratio:.2f} (under 1.0x). Spend optimization is highly advised.")
        
    # 3. Anomaly warnings
    if len(anomalies) > 3:
        warnings.append(f"High volatility warning: {len(anomalies)} anomalies were flagged in this metrics series. Confirm data source integrity.")
        
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "Analytics calculation constraints satisfy mathematical formats."
    }
