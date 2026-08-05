import re
from typing import Dict, List, Tuple, Any
from api.ai.capabilities import BaseCapability

def scan_forbidden_vocabulary(text: str, forbidden_words: List[str]) -> Tuple[List[str], List[str]]:
    """Scan copy for forbidden expressions and returns found words and rewrites."""
    found = []
    text_lower = text.lower()
    for word in forbidden_words:
        word_lower = word.lower().strip()
        if re.search(rf'\b{re.escape(word_lower)}\b', text_lower):
            found.append(word)
    return found

def check_voice_ratio(text: str) -> Dict[str, Any]:
    """
    Check active vs passive voice heuristic.
    A basic passive voice checker scans for forms of 'to be' followed by past participles (simplified heuristic).
    """
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)
    if total_words == 0:
        return {"passive_count": 0, "active_percentage": 100.0}
        
    # Simplified helper lookup passive voice forms (is/was/were/be/been/being + verb-ed)
    be_verbs = {"is", "am", "are", "was", "were", "be", "been", "being"}
    passive_matches = 0
    
    text_clean = text.lower()
    # Simple regex matches: 'is/was/were/etc + word ending in ed'
    for verb in be_verbs:
        passive_matches += len(re.findall(rf'\b{verb}\b\s+\w+ed\b', text_clean))
        
    passive_percentage = (passive_matches / len(re.split(r'[.!?]+', text)) * 100.0) if len(re.split(r'[.!?]+', text)) > 0 else 0.0
    active_percentage = max(0.0, 100.0 - passive_percentage)
    
    return {
        "passive_count": passive_matches,
        "active_percentage": round(active_percentage, 1)
    }

BRAND_CAPABILITY = BaseCapability(
    name="BRAND",
    description="Enterprise Brand voice, styling compliance, and tone regulator capability.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "forbidden_words": {"type": "array", "items": {"type": "string"}},
            "preferred_words": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["content"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "compliance_score": {"type": "number"},
            "forbidden_words_found": {"type": "array", "items": {"type": "string"}}
        }
    },
    estimated_runtime=10,
    estimated_cost=0.012,
    required_tools=["knowledge_tool"],
    required_permissions=["manage_brand"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard brand compliance rules."
)
