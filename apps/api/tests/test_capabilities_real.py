import pytest
from typing import Dict, List, Any
from api.ai.capabilities.seo.helpers import calculate_flesch_reading_ease, calculate_keyword_density
from api.ai.capabilities.seo.reflection import reflect_on_seo
from api.ai.capabilities.seo.evaluation import evaluate_seo

from api.ai.capabilities.research.helpers import normalize_monthly_price, detect_technologies_in_text
from api.ai.capabilities.research.reflection import reflect_on_research
from api.ai.capabilities.research.evaluation import evaluate_research

from api.ai.capabilities.brand.helpers import scan_forbidden_vocabulary, check_voice_ratio
from api.ai.capabilities.brand.reflection import reflect_on_brand
from api.ai.capabilities.brand.evaluation import evaluate_brand

from api.ai.capabilities.campaign.helpers import allocate_budget_heuristic
from api.ai.capabilities.campaign.reflection import reflect_on_campaign
from api.ai.capabilities.campaign.evaluation import evaluate_campaign

from api.ai.capabilities.analytics.helpers import calculate_ltv_cac_ratio, detect_anomalies_z_score
from api.ai.capabilities.analytics.reflection import reflect_on_analytics
from api.ai.capabilities.analytics.evaluation import evaluate_analytics

from api.ai.capabilities.workflow.helpers import has_cyclic_dependency
from api.ai.capabilities.workflow.reflection import reflect_on_workflow
from api.ai.capabilities.workflow.evaluation import evaluate_workflow


# --- SEO TESTS ---
def test_seo_readability_and_density():
    text = "The quick brown fox jumps over the lazy dog. This is a simple test sentence."
    # Flesch-Kincaid Ease score checks
    score = calculate_flesch_reading_ease(text)
    assert 50.0 <= score <= 100.0
    
    # Keyword density checks
    density = calculate_keyword_density(text, ["fox", "dog", "missing"])
    assert density["fox"] > 0.0
    assert density["missing"] == 0.0

def test_seo_reflection_and_evaluation():
    text = (
        "In this guide, we focus on advanced search engine optimization strategies. "
        "We discuss topic clusters, semantic keyword matching, search intent alignment, and modern SERP analysis. "
        "By building structured content layouts, enterprise marketing platforms can rank effectively. "
        "This ensures that headings, meta tags, and alt descriptions satisfy search crawlers. "
        "Furthermore, readability scores like the Flesch ease index provide insights into how readable the content is "
        "for average human users, which directly affects engagement and dwell times."
    )
    title = "Enterprise SEO Optimization and Topic Clustering Guidelines"
    desc = "Learn how to implement real SEO clustering, readability analyses, and keyword gap reports dynamically using the EAIMOS Marketing Agent Platform."
    reflection = reflect_on_seo(text, ["focus"], title, desc, ["# Focus keyword in text", "## Subheading"])
    assert reflection["valid"] is True
    
    evaluation = evaluate_seo(text, ["focus"], title, desc, ["# Focus keyword in text", "## Subheading"])
    assert evaluation["score"] > 50.0


# --- RESEARCH TESTS ---
def test_research_pricing_and_tech_stack():
    # Price normalization checks
    price_month = normalize_monthly_price(120.0, "monthly")
    price_year = normalize_monthly_price(120.0, "annual")
    assert price_month == 120.0
    assert price_year == 10.0
    
    # Tech stack lookup checks
    techs = detect_technologies_in_text("We utilize React, Next.js, Fastapi and PostgreSQL.")
    assert "React" in techs
    assert "Next.js" in techs
    assert "Fastapi" in techs

def test_research_reflection_and_evaluation():
    swot = {"strengths": ["S1", "S2"], "weaknesses": ["W1", "W2"], "opportunities": ["O1", "O2"], "threats": ["T1", "T2"]}
    pestel = {"political": ["P1"], "economic": ["E1"], "social": ["S1"], "technological": ["T1"], "environmental": ["En1"], "legal": ["L1"]}
    
    reflection = reflect_on_research(swot, pestel, 3, 2)
    assert reflection["valid"] is True
    
    evaluation = evaluate_research(swot, pestel, 3, 2)
    assert evaluation["score"] > 80.0


# --- BRAND TESTS ---
def test_brand_lexicon_and_voice():
    # Vocabulary scanner
    text = "We utilize paradigms to write content."
    found = scan_forbidden_vocabulary(text, ["utilize", "paradigms", "missing"])
    assert "utilize" in found
    assert "paradigms" in found
    assert "missing" not in found
    
    # Voice check
    voice = check_voice_ratio("This copy is written by us.")
    assert voice["active_percentage"] <= 100.0

def test_brand_reflection_and_evaluation():
    text = "We utilize paradigms to write content."
    reflection = reflect_on_brand(text, ["utilize"])
    assert reflection["valid"] is False
    
    evaluation = evaluate_brand(text, ["utilize"], 1)
    assert evaluation["score"] < 90.0


# --- CAMPAIGN TESTS ---
def test_campaign_budget_heuristic():
    performance = {
        "LinkedIn": {"ctr": 0.05, "cpc": 2.0, "cvr": 0.02},
        "Meta": {"ctr": 0.04, "cpc": 1.0, "cvr": 0.015}
    }
    allocations = allocate_budget_heuristic(5000.0, performance)
    assert len(allocations) == 2
    # Verify exact budget split sum matches total
    total_alloc = sum(a["allocated_amount"] for a in allocations)
    assert abs(total_alloc - 5000.0) < 1.0

def test_campaign_reflection_and_evaluation():
    allocations = [
        {"channel_name": "LinkedIn", "allocated_amount": 3000.0, "budget_percentage": 60.0},
        {"channel_name": "Meta", "allocated_amount": 2000.0, "budget_percentage": 40.0}
    ]
    reflection = reflect_on_campaign(5000.0, allocations, 2)
    assert reflection["valid"] is True
    
    evaluation = evaluate_campaign(5000.0, allocations, 150.0)
    assert evaluation["score"] > 80.0


# --- ANALYTICS TESTS ---
def test_analytics_metrics_and_zscore():
    # LTV to CAC checks
    ratio = calculate_ltv_cac_ratio(30.0, 0.05, 100.0)
    assert ratio == 6.0  # LTV = 30 / 0.05 = 600. Ratio = 600 / 100 = 6x.
    
    # Z-Score anomaly checks
    series = [10.0, 11.0, 10.5, 9.8, 10.2, 50.0, 10.1]
    dates = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
    anomalies = detect_anomalies_z_score(series, dates, 1.5)
    assert len(anomalies) == 1
    assert anomalies[0]["date"] == "D6"

def test_analytics_reflection_and_evaluation():
    anomalies = [{"date": "D6", "value": 50.0, "z_score": 2.3, "details": "anomaly"}]
    reflection = reflect_on_analytics(30.0, 0.05, 100.0, anomalies)
    assert reflection["valid"] is True
    
    evaluation = evaluate_analytics(30.0, 0.05, 100.0, 1, 3)
    assert evaluation["score"] > 80.0


# --- WORKFLOW TESTS ---
def test_workflow_dag_cycles():
    # 1. No cycles (Valid DAG)
    valid_steps = [
        {"step_id": "step1", "action_type": "trigger", "depends_on": []},
        {"step_id": "step2", "action_type": "action", "depends_on": ["step1"]},
        {"step_id": "step3", "action_type": "action", "depends_on": ["step2"]}
    ]
    assert has_cyclic_dependency(valid_steps) is False
    
    # 2. Cycle present (Invalid DAG)
    invalid_steps = [
        {"step_id": "step1", "action_type": "action", "depends_on": ["step3"]},
        {"step_id": "step2", "action_type": "action", "depends_on": ["step1"]},
        {"step_id": "step3", "action_type": "action", "depends_on": ["step2"]}
    ]
    assert has_cyclic_dependency(invalid_steps) is True

def test_workflow_reflection_and_evaluation():
    steps = [
        {"step_id": "step1", "action_type": "trigger", "depends_on": []},
        {"step_id": "step2", "action_type": "action", "depends_on": ["step1"]}
    ]
    reflection = reflect_on_workflow(steps)
    assert reflection["valid"] is True
    
    evaluation = evaluate_workflow(steps)
    assert evaluation["score"] > 80.0
