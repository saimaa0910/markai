import re
from typing import Dict, List, Any
from api.ai.capabilities import BaseCapability

def count_syllables_in_word(word: str) -> int:
    word = word.lower().strip()
    if not word:
        return 0
    
    # Syllables vowel lookup logic
    vowels = "aeiouy"
    count = 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count <= 0:
        count = 1
    return count

def calculate_flesch_reading_ease(text: str) -> float:
    """
    Calculate Flesch Reading Ease score.
    Formula: 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_sentences = len(sentences)
    
    # Normalize words list
    words = re.findall(r'\b\w+\b', text)
    total_words = len(words)
    
    if total_words == 0 or total_sentences == 0:
        return 100.0
        
    total_syllables = sum(count_syllables_in_word(w) for w in words)
    
    asl = total_words / total_sentences
    asw = total_syllables / total_words
    
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return max(0.0, min(100.0, score))

def calculate_keyword_density(text: str, target_keywords: List[str]) -> Dict[str, float]:
    """Calculate the frequency density of keywords in content text."""
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)
    if total_words == 0:
        return {kw: 0.0 for kw in target_keywords}
        
    density = {}
    for kw in target_keywords:
        kw_lower = kw.lower()
        # Find occurrences of keyword (handling multi-word terms)
        occurrences = len(re.findall(rf'\b{re.escape(kw_lower)}\b', text.lower()))
        density[kw] = (occurrences / total_words) * 100.0
    return density

SEO_CAPABILITY = BaseCapability(
    name="SEO",
    description="Enterprise SEO optimization capability. Runs SERP reviews, readability analyses, schemas, and keyword clustering.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "target_keywords": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["content"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "seo_score": {"type": "number"},
            "readability_score": {"type": "number"},
            "density": {"type": "object"}
        }
    },
    estimated_runtime=12,
    estimated_cost=0.015,
    required_tools=["web_search_tool", "knowledge_tool", "analytics_tool"],
    required_permissions=["manage_seo"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard enterprise SEO guidelines."
)
