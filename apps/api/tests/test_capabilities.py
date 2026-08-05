import pytest
from api.ai.capabilities.registry import CapabilityRegistry

def test_capability_metadata():
    CapabilityRegistry.initialize()
    for cap_name in ["SEO", "RESEARCH", "CAMPAIGN", "ANALYTICS", "BRAND", "WORKFLOW"]:
        cap = CapabilityRegistry.load(cap_name)
        assert cap.name == cap_name
        assert cap.estimated_runtime > 0
        assert cap.estimated_cost >= 0.0
        assert len(cap.input_schema["properties"]) > 0
        assert len(cap.output_schema["properties"]) > 0
        assert cap.get_system_instructions() is not None
