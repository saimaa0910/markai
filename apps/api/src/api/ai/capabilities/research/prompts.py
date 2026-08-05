# Research Capability Prompts

SYSTEM_PROMPT = """You are a Principal Market Research Analyst and Enterprise SaaS Architect.
You compile competitor intelligence, technographic lookups, SWOT reports, PESTEL matrices, pricing structures, and ICP personas.
"""

PLANNER_PROMPT = """Decompose the user's research request.
1. Outline PESTEL dimensions relevant to the target company.
2. Outline competitor pricing matrices.
3. Identify pain points for target ICP personas.
4. Construct SWOT profiles.
"""

EXECUTION_PROMPT = """Analyze the company '{company_name}' in the '{industry}' industry against competitors: {competitors}.
Identify:
- SWOT parameters.
- PESTEL influences.
- Pricing plans.
- Technographic stacks.
"""

REFLECTION_PROMPT = """Verify the quality of the compiled research report:
- Verify that strengths, weaknesses, opportunities, and threats are all non-empty.
- Verify that PESTEL dimensions are populated with descriptive items.
- Check source citations validity.
"""

EVALUATION_PROMPT = """Grade the market research output:
- Source coverage index.
- Completeness of competitor pricing structures.
- SWOT balance grade.
- Persona alignment accuracy.
"""

REWRITE_PROMPT = """Rewrite the market report to resolve this critique:
{critique}
Original report content:
{content}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "SWOT for Slack in enterprise messaging",
        "output": {
            "strengths": ["Huge brand recognition", "Smooth API integrations ecosystem"],
            "weaknesses": ["High per-user price tiering compared to MS Teams"],
            "opportunities": ["Generative summaries inside channels"],
            "threats": ["MS Teams bundled with Office 365 standard seats"]
        }
    }
]
