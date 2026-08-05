from typing import Dict, Any, List
from api.ai.capabilities.brand.helpers import scan_forbidden_vocabulary, check_voice_ratio

def reflect_on_brand(
    text: str,
    forbidden_words: List[str]
) -> Dict[str, Any]:
    """Check style guidelines and forbidden word violations."""
    warnings = []
    
    # 1. Scan vocabulary
    found_forbidden = scan_forbidden_vocabulary(text, forbidden_words)
    if found_forbidden:
        warnings.append(f"Forbidden vocabulary warning: The following prohibited expressions were detected: {found_forbidden}.")
        
    # 2. Check passive voice levels
    voice = check_voice_ratio(text)
    if voice["active_percentage"] < 70.0:
        warnings.append(f"Passive voice warning: The copy has a high passive voice percentage (Active: {voice['active_percentage']}%). Try using active verbs.")
        
    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "critique": "\n".join(warnings) if warnings else "Brand compliance passes successfully."
    }
