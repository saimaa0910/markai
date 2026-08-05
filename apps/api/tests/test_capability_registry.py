import pytest
from api.ai.capabilities.registry import CapabilityRegistry
from api.ai.capabilities import BaseCapability

@pytest.fixture(autouse=True)
def clean_registry():
    CapabilityRegistry._registry = {}
    CapabilityRegistry._initialized = False
    yield

def test_capability_registration_and_load():
    cap = BaseCapability(
        name="TEST_CAP",
        description="A capability for testing",
        input_schema={},
        output_schema={}
    )
    CapabilityRegistry.register(cap)
    assert CapabilityRegistry.load("TEST_CAP") == cap
    assert "TEST_CAP" in CapabilityRegistry.list()

def test_capability_initialization():
    CapabilityRegistry.initialize()
    assert len(CapabilityRegistry.discover()) > 0
    assert "SEO" in CapabilityRegistry.list()
    assert "RESEARCH" in CapabilityRegistry.list()
