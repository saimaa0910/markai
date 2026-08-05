# SEO Capability Prompts

SYSTEM_PROMPT = """You are an expert Enterprise SEO Specialist and Content Optimizer.
Your job is to optimize content to rank in position 1 on SERPs.
You analyze search intent, competitor gaps, readability metrics, headings hierarchy, and schema.org requirements.
"""

PLANNER_PROMPT = """Decompose the user's SEO request.
1. Identify primary search intent (Informational, Transactional, Navigational).
2. Establish key competitor gaps based on target tags.
3. Construct FAQ schema requirements.
4. Plan heading structures (H1, H2, H3).
"""

EXECUTION_PROMPT = """Optimize the following text for these primary keywords: {keywords}.
Content:
{content}
Ensure:
- Focus keyword in H1 and first paragraph.
- Meta title length is between 50-60 characters.
- Meta description length is between 120-160 characters.
- JSON-LD FAQ schema is generated.
"""

REFLECTION_PROMPT = """Critique the generated content for SEO compliance:
- Check for keyword stuffing (keyword density > 3% is penalized).
- Check if headings nesting order is valid (H1 -> H2 -> H3).
- Check if meta title and description lengths are within limits.
"""

EVALUATION_PROMPT = """Grade the optimized SEO content:
- Keyword match score (0.0 to 1.0).
- Readability ease level (Flesch ease grade).
- Meta metadata accuracy.
- Structure grade.
"""

REWRITE_PROMPT = """Rewrite the text to resolve the following SEO critique:
{critique}
Original Content:
{content}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Optimize 'Viptant releases AI platform'",
        "output": {
            "meta_title": "Viptant Releases Enterprise AI Platform | 2026 Core Solutions",
            "meta_description": "Viptant announces its flagship AI Gateway and agent workflows platform to accelerate enterprise automation. Learn more about it today.",
            "headings": ["# Viptant Releases Enterprise AI Platform", "## Core Agent Runtime Capabilities", "### Dynamic Memory and Gateway Routing"],
            "score": 95.0
        }
    }
]
