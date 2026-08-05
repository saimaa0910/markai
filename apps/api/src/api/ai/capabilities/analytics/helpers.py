import math
from typing import Dict, List, Any
from api.ai.capabilities import BaseCapability

def calculate_ltv_cac_ratio(arpu: float, churn_rate: float, cac: float) -> float:
    """
    Calculate LTV to CAC ratio.
    LTV = ARPU / Churn Rate
    Ratio = LTV / CAC
    """
    if churn_rate <= 0.0 or cac <= 0.0:
        return 0.0
    ltv = arpu / churn_rate
    return round(ltv / cac, 2)

def detect_anomalies_z_score(
    values: List[float],
    dates: List[str],
    threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Identify outlier metrics using a standardized Z-Score algorithm.
    Z = (x - mean) / std_dev
    """
    n = len(values)
    if n < 3:
        return []
        
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)
    
    if std_dev == 0.0:
        return []
        
    anomalies = []
    for idx, x in enumerate(values):
        z = (x - mean) / std_dev
        if abs(z) > threshold:
            anomalies.append({
                "date": dates[idx],
                "value": x,
                "z_score": round(z, 2),
                "details": f"Outlier detected: value {x} is {z:.2f} standard deviations away from the mean ({mean:.2f})."
            })
            
    return anomalies

ANALYTICS_CAPABILITY = BaseCapability(
    name="ANALYTICS",
    description="Enterprise Analytics, CAC/LTV cohorts, attribution modeling, forecast dashboards, and anomaly detectors.",
    input_schema={
        "type": "object",
        "properties": {
            "metrics_series": {"type": "array", "items": {"type": "number"}},
            "dates_series": {"type": "array", "items": {"type": "string"}},
            "arpu": {"type": "number"},
            "churn_rate": {"type": "number"},
            "cac": {"type": "number"}
        },
        "required": ["metrics_series", "dates_series"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "ltv_cac_ratio": {"type": "number"},
            "anomalies": {"type": "array", "items": {"type": "object"}}
        }
    },
    estimated_runtime=15,
    estimated_cost=0.018,
    required_tools=["analytics_tool", "calculator_tool"],
    required_permissions=["manage_analytics"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard enterprise analytics reporting instructions."
)
