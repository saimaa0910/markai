from typing import Dict, List, Any
from api.ai.capabilities import BaseCapability

def normalize_monthly_price(price: float, cycle: str) -> float:
    """Normalize plan prices to a standard monthly billing interval."""
    cycle_clean = cycle.lower().strip()
    if "year" in cycle_clean or "annual" in cycle_clean:
        return round(price / 12.0, 2)
    return round(price, 2)

def detect_technologies_in_text(text: str) -> List[str]:
    """Identify enterprise software stacks from competitor profiles."""
    tech_directory = [
        "react", "next.js", "typescript", "javascript", "angular", "vue",
        "python", "fastapi", "django", "flask", "ruby", "rails", "php", "laravel",
        "postgresql", "mongodb", "redis", "mysql", "sqlite", "elasticsearch",
        "docker", "kubernetes", "aws", "gcp", "azure", "stripe", "salesforce",
        "hubspot", "segment", "amplitude", "mixpanel", "openai", "pinecone",
        "langchain", "terraform", "github", "gitlab", "jira", "confluence"
    ]
    
    found = []
    text_lower = text.lower()
    for tech in tech_directory:
        if tech in text_lower:
            # Format nicely
            if tech == "next.js":
                found.append("Next.js")
            elif tech == "gcp":
                found.append("Google Cloud Platform (GCP)")
            elif tech == "aws":
                found.append("Amazon Web Services (AWS)")
            else:
                found.append(tech.capitalize())
    return found

RESEARCH_CAPABILITY = BaseCapability(
    name="RESEARCH",
    description="Enterprise Market and Competitor Research capability. Pulls SWOT models, pricing comparisons, tech stacks, and buyer journey funnels.",
    input_schema={
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "competitors": {"type": "array", "items": {"type": "string"}},
            "industry": {"type": "string"}
        },
        "required": ["company_name"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "technographic_stack": {"type": "array", "items": {"type": "string"}},
            "report_summary": {"type": "string"}
        }
    },
    estimated_runtime=25,
    estimated_cost=0.035,
    required_tools=["web_search_tool", "knowledge_tool", "calculator_tool"],
    required_permissions=["manage_research"],
    supports_delegation=True,
    supports_parallel_execution=True,
    prompt_template="Standard market research protocols."
)
