# Brand Capability Prompts

SYSTEM_PROMPT = """You are a Brand Voice Director and Copy Editor.
You evaluate marketing copy for brand voice compliance, style consistency, vocabulary rules, forbidden words, and tone alignment.
"""

PLANNER_PROMPT = """Plan brand audit checks:
1. Scan copy for forbidden words lists.
2. Grade passive vs active voice levels.
3. Check mission alignment and tone guidelines.
"""

EXECUTION_PROMPT = """Audit the following text for style and voice rules.
Content:
{content}
Forbidden words lists: {forbidden_words}
Preferred replacement suggestions: {preferred_words}
"""

REFLECTION_PROMPT = """Critique tone compliance:
- Check for tone consistency (is it overly salesy or informal?).
- Check passive verbs percentage.
- Verify forbidden vocab is completely omitted.
"""

EVALUATION_PROMPT = """Grade Brand compliance metrics:
- Tone matching score.
- Forbidden vocabulary count.
- Suggested edits counts.
"""

REWRITE_PROMPT = """Rewrite the text to comply with the brand style guidelines:
{critique}
Original text:
{content}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "We utilize standard paradigms to optimize performance.",
        "output": {
            "brand_score": 80.0,
            "forbidden_words_found": ["utilize", "paradigms"],
            "suggestions": ["Use 'use' instead of 'utilize'.", "Avoid buzzwords like 'paradigms'."]
        }
    }
]
