# Analytics Capability Prompts

SYSTEM_PROMPT = """You are a Principal Marketing Analytics and Revenue Operations Specialist.
You audit CAC, LTV, conversion funnels, attribution weight splits, cohort tables, and run anomaly detections.
"""

PLANNER_PROMPT = """Plan analytics dashboards parsing:
1. Identify LTV/CAC viability index.
2. Locate ad spend anomalies.
3. Establish funnel conversion drop-offs.
4. Draft executive highlights.
"""

EXECUTION_PROMPT = """Evaluate marketing metrics with ARPU: {arpu}, Churn Rate: {churn_rate}, CAC: {cac}.
Input values series: {metrics_series} with dates: {dates_series}.
Analyze anomalies and construct LTV cohorts.
"""

REFLECTION_PROMPT = """Critique analytics checks:
- Verify that forecast formulas are mathematically consistent.
- Check cohort percentages formatting correctness.
- Audit Z-score threshold levels.
"""

EVALUATION_PROMPT = """Grade analytics outputs:
- Forecast accuracy ratio.
- Math validation correctness score.
- Insight clarity score.
"""

REWRITE_PROMPT = """Rewrite the analytics executive report to correct formatting issues:
{critique}
Original report copy:
{content}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "CAC $100, ARPU $30, Churn 5%",
        "output": {
            "ltv_cac_ratio": 6.0,
            "roas": 3.5,
            "executive_insights": ["LTV/CAC ratio is 6x, indicating highly healthy unit economics."]
        }
    }
]
