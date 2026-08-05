import pytest
from pydantic import ValidationError
from api.ai.agents.base.manifest import AgentManifest
from api.ai.agents.base.policies import AgentPolicies
from api.ai.agents.base.permissions import AgentPermissions
from api.ai.agents.base.metadata import AgentMetadata
from api.ai.agents.base.constants import AgentStatus

def test_manifest_validation_success():
    manifest_data = {
        "id": "TEST_AGENT",
        "name": "Test Agent",
        "description": "A test agent manifest.",
        "category": "MARKETING",
        "metadata": {
            "icon": "🤖",
            "gradient": "from-blue-500 to-indigo-500",
            "accent_color": "#3b82f6",
            "category": "MARKETING",
            "description": "A test agent manifest.",
            "status": "STABLE"
        }
    }
    
    manifest = AgentManifest(**manifest_data)
    assert manifest.id == "TEST_AGENT"
    assert manifest.metadata.status == AgentStatus.STABLE
    assert manifest.policies.temperature == 0.7  # Default value

def test_manifest_validation_missing_fields():
    with pytest.raises(ValidationError):
        # Missing name and metadata description
        AgentManifest(id="TEST")
