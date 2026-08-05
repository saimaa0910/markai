import pytest
from api.ai.agents.base.permissions import AgentPermissions

def test_permissions_defaults():
    perms = AgentPermissions()
    assert perms.allowed_tools == []
    assert perms.allowed_organizations == ["*"]
    assert perms.allowed_roles == ["*"]
    assert perms.allowed_users == ["*"]

def test_permissions_custom():
    perms = AgentPermissions(
        allowed_tools=["calculator_tool", "web_search_tool"],
        allowed_roles=["ADMIN", "OWNER"]
    )
    assert "calculator_tool" in perms.allowed_tools
    assert perms.allowed_roles == ["ADMIN", "OWNER"]
