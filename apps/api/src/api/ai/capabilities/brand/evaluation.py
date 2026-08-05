from typing import Dict, Any, List
from api.ai.capabilities.brand.helpers import scan_forbidden_vocabulary, check_voice_ratio

def evaluate_brand(
    text: str,
    forbidden_words: List[str],
    tone_violations_count: int
) -> Dict[str, Any]:
    """Calculate dedicated Brand score metrics."""
    # 1. Vocab compliance (Max 40 points)
    found_forbidden = scan_forbidden_vocabulary(text, forbidden_words)
    vocab_score = max(0.0, 40.0 - (len(found_forbidden) * 10.0))
    
    # 2. Tone compliance (Max 30 points)
    tone_score = max(0.0, 30.0 - (tone_violations_count * 10.0))
    
    # 3. Active voice (Max 30 points)
    voice = check_voice_ratio(text)
    active_ratio = voice["active_percentage"]  # 0 to 100
    voice_score = (active_ratio / 100.0) * 30.0
    
    total_score = vocab_score + tone_score + voice_score
    
    return {
        "score": round(total_score, 1),
        "metrics": {
            "vocabulary_compliance": round(vocab_score / 40.0 * 100.0, 1) if vocab_score > 0 else 0.0,
            "tone_compliance": round(tone_score / 30.0 * 100.0, 1) if tone_score > 0 else 0.0,
            "active_voice_rating": round(voice_score / 30.0 * 100.0, 1) if voice_score > 0 else 0.0
        }
    }
