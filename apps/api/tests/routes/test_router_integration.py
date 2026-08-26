"""
Sprint 7 FastAPI Router Integration Tests
===========================================
Tests for FastAPI router endpoints invoking domain services.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.base.service_result import ServiceResult
from api.services.core.dependencies import get_organization_service


client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_organization_route_service_integration():
    mock_org_service = AsyncMock()
    mock_org = MagicMock()
    mock_org.id = uuid.uuid4()
    mock_org.name = "Enterprise Corp"
    mock_org.slug = "enterprise-corp"
    mock_org.plan_tier = "starter"
    mock_org.max_members = 10
    mock_org.is_active = True
    mock_org.created_at = None

    mock_org_service.create.return_value = ServiceResult.ok(data=mock_org, status_code=201)

    app.dependency_overrides[get_organization_service] = lambda: mock_org_service

    # Override get_current_user
    from api.core.deps import get_current_user
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Override the Sprint 8.3.1 auth-enforcement dependency (service wiring test)
    from api.middleware.auth_enforcement import enforce_all_auth_policies as enforce_all
    app.dependency_overrides[enforce_all] = lambda: None

    try:
        response = client.post(
            "/api/v1/organizations/",
            json={"name": "Enterprise Corp", "slug": "enterprise-corp"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Enterprise Corp"
        assert mock_org_service.create.called
    finally:
        app.dependency_overrides.clear()


def test_create_prompt_route_service_integration():
    from api.services.ai import get_prompt_service
    from api.models.membership import UserOrganization, UserRole

    mock_org_id = uuid.uuid4()
    mock_prompt_service = AsyncMock()
    mock_prompt = MagicMock()
    mock_prompt.id = uuid.uuid4()
    mock_prompt.organization_id = mock_org_id
    mock_prompt.title = "Sales Outreach"
    mock_prompt.template = "Hello {{name}}"
    mock_prompt.description = "Sales template"
    mock_prompt.version = 1
    mock_prompt.is_active = True
    mock_prompt.created_at = None

    mock_prompt_service.create_prompt.return_value = ServiceResult.ok(data=mock_prompt, status_code=201)

    app.dependency_overrides[get_prompt_service] = lambda: mock_prompt_service

    # Override active_member dependency
    from api.routes.prompts import active_member
    mock_membership = MagicMock()
    mock_membership.user_id = uuid.uuid4()
    mock_membership.organization_id = uuid.uuid4()
    mock_membership.role = UserRole.ADMIN
    app.dependency_overrides[active_member] = lambda: mock_membership

    # Override the Sprint 8.3.1 auth-enforcement dependency (service wiring test)
    from api.middleware.auth_enforcement import enforce_all_auth_policies as enforce_all
    app.dependency_overrides[enforce_all] = lambda: None

    try:
        response = client.post(
            "/api/v1/prompts/",
            json={"name": "Sales Outreach", "content": "Hello {{name}}"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Sales Outreach"
        assert mock_prompt_service.create_prompt.called
    finally:
        app.dependency_overrides.clear()
