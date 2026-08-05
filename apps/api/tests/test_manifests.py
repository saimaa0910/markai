import pytest
from api.ai.agents.seo.manifest import SEO_AGENT_MANIFEST
from api.ai.agents.research.manifest import RESEARCH_AGENT_MANIFEST
from api.ai.agents.campaign.manifest import CAMPAIGN_AGENT_MANIFEST
from api.ai.agents.analytics.manifest import ANALYTICS_AGENT_MANIFEST
from api.ai.agents.brand.manifest import BRAND_AGENT_MANIFEST
from api.ai.agents.workflow.manifest import WORKFLOW_AGENT_MANIFEST

def test_manifest_strategies():
    assert SEO_AGENT_MANIFEST.memory_strategy == "window"
    assert SEO_AGENT_MANIFEST.planner_strategy == "sequential"
    assert SEO_AGENT_MANIFEST.evaluation_strategy == "seo"

    assert RESEARCH_AGENT_MANIFEST.memory_strategy == "session"
    assert RESEARCH_AGENT_MANIFEST.planner_strategy == "reactive"
    assert RESEARCH_AGENT_MANIFEST.evaluation_strategy == "research"

    assert CAMPAIGN_AGENT_MANIFEST.memory_strategy == "hybrid"
    assert CAMPAIGN_AGENT_MANIFEST.planner_strategy == "hierarchical"
    assert CAMPAIGN_AGENT_MANIFEST.evaluation_strategy == "campaign"

    assert ANALYTICS_AGENT_MANIFEST.memory_strategy == "organization"
    assert ANALYTICS_AGENT_MANIFEST.planner_strategy == "reflective"
    assert ANALYTICS_AGENT_MANIFEST.evaluation_strategy == "analytics"

    assert BRAND_AGENT_MANIFEST.memory_strategy == "knowledge"
    assert BRAND_AGENT_MANIFEST.planner_strategy == "reactive"
    assert BRAND_AGENT_MANIFEST.evaluation_strategy == "brand"

    assert WORKFLOW_AGENT_MANIFEST.memory_strategy == "session"
    assert WORKFLOW_AGENT_MANIFEST.planner_strategy == "react"
    assert WORKFLOW_AGENT_MANIFEST.evaluation_strategy == "workflow"
