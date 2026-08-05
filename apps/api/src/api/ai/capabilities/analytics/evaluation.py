from typing import Dict, Any, List
from api.ai.capabilities.analytics.helpers import calculate_ltv_cac_ratio

def evaluate_analytics(
    arpu: float,
    churn_rate: float,
    cac: float,
    anomalies_count: int,
    insights_count: int
) -> Dict[str, Any]:
    """Grade analytics insights and calculation correctness."""
    # 1. Math verification score (Max 40 points)
    ratio = calculate_ltv_cac_ratio(arpu, churn_rate, cac)
    math_score = 40.0
    if ratio <= 0.0:
        math_score -= 20.0
    if churn_rate <= 0.0 or churn_rate > 1.0:
        math_score -= 20.0
        
    # 2. Insight depth (Max 30 points)
    insight_score = min(30.0, insights_count * 10.0)
    
    # 3. Anomaly coverage (Max 30 points)
    # Volatility penalty if data has too many anomalies without explanation
    volatility_score = 30.0
    if anomalies_count > 5:
        volatility_score -= 15.0
        
    total_score = math_score + insight_score + volatility_score
    
    return {
        "score": round(total_score, 1),
        "metrics": {
            "mathematical_correctness": round(math_score / 40.0 * 100.0, 1) if math_score > 0 else 0.0,
            "insight_depth_score": round(insight_score / 30.0 * 100.0, 1) if insight_score > 0 else 0.0,
            "volatility_resilience": round(volatility_score / 30.0 * 100.0, 1) if volatility_score > 0 else 0.0
        }
    }
