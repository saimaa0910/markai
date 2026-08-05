from typing import Dict, Any, List
from api.ai.capabilities.seo.helpers import calculate_flesch_reading_ease, calculate_keyword_density

def evaluate_seo(
    text: str,
    keywords: List[str],
    meta_title: str,
    meta_desc: str,
    headings: List[str]
) -> Dict[str, Any]:
    """Calculate dedicated SEO evaluation metrics."""
    # 1. Readability
    readability = calculate_flesch_reading_ease(text)
    
    # 2. Keyword score (fraction of target keywords present)
    density = calculate_keyword_density(text, keywords)
    present_keywords = sum(1 for v in density.values() if v > 0.0)
    keyword_score = (present_keywords / len(keywords) * 100.0) if keywords else 100.0
    
    # 3. Meta score
    title_valid = 40 <= len(meta_title) <= 65
    desc_valid = 110 <= len(meta_desc) <= 170
    meta_score = 100.0
    if not title_valid:
        meta_score -= 40.0
    if not desc_valid:
        meta_score -= 40.0
        
    # 4. Structure score
    has_h1 = any(h.startswith("# ") or h.lower().startswith("h1") for h in headings)
    has_h2 = any(h.startswith("## ") or h.lower().startswith("h2") for h in headings)
    struct_score = 100.0
    if not has_h1:
        struct_score -= 50.0
    if not has_h2:
        struct_score -= 20.0
        
    # Final SEO Score
    final_score = (readability * 0.2) + (keyword_score * 0.3) + (meta_score * 0.25) + (struct_score * 0.25)
    
    return {
        "score": round(final_score, 1),
        "metrics": {
            "keyword_score": round(keyword_score, 1),
            "readability": round(readability, 1),
            "meta_score": round(meta_score, 1),
            "structure_score": round(struct_score, 1)
        }
    }
