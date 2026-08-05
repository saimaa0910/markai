import pytest
from api.ai.agents.base.policies import AgentPolicies

def test_policies_defaults():
    policies = AgentPolicies()
    assert "gpt-4o" in policies.allowed_models
    assert policies.temperature == 0.7
    assert policies.max_runtime_sec == 300
    assert policies.max_iterations == 10
    assert policies.streaming is True

def test_policies_custom():
    policies = AgentPolicies(
        allowed_models=["custom-model"],
        temperature=0.9,
        max_cost=15.0
    )
    assert policies.allowed_models == ["custom-model"]
    assert policies.temperature == 0.9
    assert policies.max_cost == 15.0
