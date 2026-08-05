from typing import Dict, Any, List

def evaluate_research(
    swot: Dict[str, List[str]],
    pestel: Dict[str, List[str]],
    pricing_count: int,
    persona_points: int
) -> Dict[str, Any]:
    """Grade the research output on completeness and coverage."""
    # 1. SWOT balance (Max 30 points)
    swot_score = 0.0
    for key in ["strengths", "weaknesses", "opportunities", "threats"]:
        if len(swot.get(key, [])) >= 2:
            swot_score += 7.5
        elif len(swot.get(key, [])) > 0:
            swot_score += 4.0
            
    # 2. PESTEL coverage (Max 30 points)
    pestel_score = 0.0
    for dim in ["political", "economic", "social", "technological", "environmental", "legal"]:
        if len(pestel.get(dim, [])) >= 1:
            pestel_score += 5.0
            
    # 3. Pricing & ICP details (Max 40 points)
    pricing_score = min(20.0, pricing_count * 10.0)
    persona_score = min(20.0, persona_points * 5.0)
    
    total_score = swot_score + pestel_score + pricing_score + persona_score
    
    return {
        "score": round(total_score, 1),
        "metrics": {
            "swot_balance": round(swot_score / 30.0 * 100.0, 1) if swot_score > 0 else 0.0,
            "pestel_coverage": round(pestel_score / 30.0 * 100.0, 1) if pestel_score > 0 else 0.0,
            "pricing_completeness": round(pricing_score / 20.0 * 100.0, 1) if pricing_score > 0 else 0.0,
            "persona_depth": round(persona_score / 20.0 * 100.0, 1) if persona_score > 0 else 0.0
        }
    }
