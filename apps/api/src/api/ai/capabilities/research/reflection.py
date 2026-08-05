from typing import Dict, Any, List

def reflect_on_research(
    swot: Dict[str, List[str]],
    pestel: Dict[str, List[str]],
    pricing_count: int,
    persona_points: int
) -> Dict[str, Any]:
    """Audit research report structure and flag missing segments."""
    warnings = []
    
    # 1. SWOT coverage
    for key in ["strengths", "weaknesses", "opportunities", "threats"]:
        items = swot.get(key, [])
        if not items:
            warnings.append(f"SWOT is incomplete: missing '{key}' list.")
        elif len(items) < 2:
            warnings.append(f"SWOT '{key}' list is sparse. Try listing at least 2 distinct parameters.")
            
    # 2. PESTEL coverage
    dimensions = ["political", "economic", "social", "technological", "environmental", "legal"]
    for dim in dimensions:
        items = pestel.get(dim, [])
        if not items:
            warnings.append(f"PESTEL is incomplete: missing '{dim}' context items.")
            
    # 3. Pricing coverage
    if pricing_count == 0:
        warnings.append("No competitor pricing plans detected. Research should identify market price anchors.")
        
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "Research compilation meets factual completeness."
    }
