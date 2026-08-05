from typing import Dict, Any, List
from api.ai.capabilities.seo.helpers import calculate_keyword_density

def reflect_on_seo(
    text: str,
    keywords: List[str],
    meta_title: str,
    meta_desc: str,
    headings: List[str]
) -> Dict[str, Any]:
    """
    Check SEO compliance and return warnings/critiques.
    """
    warnings = []
    
    # 1. Title length check (ideal: 50-60 chars)
    if len(meta_title) < 40 or len(meta_title) > 65:
        warnings.append(f"Meta title length ({len(meta_title)} chars) is outside the ideal 40-65 character range.")
        
    # 2. Description length check (ideal: 120-160 chars)
    if len(meta_desc) < 110 or len(meta_desc) > 170:
        warnings.append(f"Meta description length ({len(meta_desc)} chars) is outside the ideal 110-170 character range.")
        
    # 3. Density check (ideal: 0.5% - 2.5%)
    density = calculate_keyword_density(text, keywords)
    for kw, val in density.items():
        if val > 3.0:
            warnings.append(f"Keyword stuffing warning: '{kw}' has a density of {val:.2f}%, exceeding the 3.0% penalty threshold.")
        elif val < 0.5:
            warnings.append(f"Under-optimization warning: '{kw}' has a density of only {val:.2f}%. Try including it more naturally.")
            
    # 4. Heading structure check
    has_h1 = any(h.startswith("# ") or h.lower().startswith("h1") for h in headings)
    if not has_h1:
        warnings.append("Missing H1 heading. Content should have exactly one H1 header.")
        
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "SEO compliance passes successfully."
    }
