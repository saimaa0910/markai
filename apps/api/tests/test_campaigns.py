import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_campaigns_lifecycle_and_tenant_isolation():
    """
    Verify complete Campaign lifecycle: creation, state machine validation,
    execution simulation, tracking metrics, and strict tenant security isolation.
    """
    # 1. Register and login User A (creates Org A)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a_camp@example.com",
            "password": "superpassword123",
            "full_name": "User A Camp",
            "org_name": "Org A Camp",
        },
    )
    login_a = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a_camp@example.com", "password": "superpassword123"},
    ).json()
    token_a = login_a["access_token"]

    # Retrieve Org A details
    orgs_a = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    org_a_id = orgs_a[0]["id"]

    # 2. Register and login User B (creates Org B)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b_camp@example.com",
            "password": "superpassword123",
            "full_name": "User B Camp",
            "org_name": "Org B Camp",
        },
    )
    login_b = client.post(
        "/api/v1/auth/login",
        data={"username": "user_b_camp@example.com", "password": "superpassword123"},
    ).json()
    token_b = login_b["access_token"]

    # Retrieve Org B details
    orgs_b = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    org_b_id = orgs_b[0]["id"]

    # 3. Create Campaign A under Org A (Draft status)
    campaign_payload_a = {
        "title": "Email Newsletter Q3",
        "description": "Quarterly newsletter for enterprise clients",
        "budget": 2500.00,
        "channel": "EMAIL",
        "template": {
            "title": "Q3 Email Template",
            "subject": "Exclusive Updates for Q3",
            "content_a": "Hi, check out our variant A updates!",
            "content_b": "Hi, check out our variant B highlights!",
        },
    }
    create_res_a = client.post(
        "/api/v1/campaigns/",
        json=campaign_payload_a,
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert create_res_a.status_code == 201
    campaign_a = create_res_a.json()
    assert campaign_a["title"] == "Email Newsletter Q3"
    assert campaign_a["status"] == "DRAFT"
    assert campaign_a["organization_id"] == org_a_id
    assert campaign_a["template"]["subject"] == "Exclusive Updates for Q3"
    assert campaign_a["analytics"]["impressions_a"] == 0

    # 4. Create Campaign B under Org A (Scheduled status)
    campaign_payload_b = {
        "title": "Scheduled Ads Promo",
        "budget": 1200.00,
        "channel": "ADS",
        "scheduled_for": "2026-08-01T12:00:00Z",
        "template": {
            "title": "Banner Ads",
            "content_a": "Buy now!",
        },
    }
    create_res_b = client.post(
        "/api/v1/campaigns/",
        json=campaign_payload_b,
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert create_res_b.status_code == 201
    campaign_b = create_res_b.json()
    assert campaign_b["status"] == "SCHEDULED"

    # 5. Check campaign listing under Org B (should be isolated/empty)
    list_res_b = client.get(
        "/api/v1/campaigns/",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert list_res_b.status_code == 200
    assert len(list_res_b.json()) == 0

    # 6. Check campaign listing under Org A (should contain 2 campaigns)
    list_res_a = client.get(
        "/api/v1/campaigns/",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert list_res_a.status_code == 200
    assert len(list_res_a.json()) == 2

    # 7. User B tries to view Campaign A (should return 404 Not Found to prevent leakage)
    blocked_get = client.get(
        f"/api/v1/campaigns/{campaign_a['id']}",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert blocked_get.status_code == 404

    # 8. User B tries to update Campaign A (should return 404 Not Found)
    blocked_put = client.put(
        f"/api/v1/campaigns/{campaign_a['id']}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert blocked_put.status_code == 404

    # 9. Update Campaign A (User A) - Validate invalid state transition
    # Transitioning DRAFT -> COMPLETED is invalid (must go through ACTIVE)
    invalid_transition = client.put(
        f"/api/v1/campaigns/{campaign_a['id']}",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert invalid_transition.status_code == 400

    # Valid update (change title and budget)
    valid_update = client.put(
        f"/api/v1/campaigns/{campaign_a['id']}",
        json={"title": "Updated Newsletter Q3", "budget": 3000.00},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert valid_update.status_code == 200
    assert valid_update.json()["title"] == "Updated Newsletter Q3"
    assert float(valid_update.json()["budget"]) == 3000.00

    # 10. Simulate Run Execution on Campaign A (Draft -> Active)
    execution_res = client.post(
        f"/api/v1/campaigns/{campaign_a['id']}/execute",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert execution_res.status_code == 200
    executed_camp = execution_res.json()
    assert executed_camp["status"] == "ACTIVE"
    # Initial simulated metrics should be populated
    assert executed_camp["analytics"]["impressions_a"] == 1200
    assert executed_camp["analytics"]["clicks_b"] == 150
    assert float(executed_camp["analytics"]["revenue"]) == 850.00

    # 11. Track events under active Campaign A
    # Track click on Variant B
    track_res_1 = client.post(
        f"/api/v1/campaigns/{campaign_a['id']}/track",
        json={"variant": "B", "event_type": "click"},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert track_res_1.status_code == 200
    assert track_res_1.json()["analytics"]["clicks_b"] == 151

    # Track conversion on Variant A with revenue generated
    track_res_2 = client.post(
        f"/api/v1/campaigns/{campaign_a['id']}/track",
        json={"variant": "A", "event_type": "conversion", "revenue_generated": 150.50},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert track_res_2.status_code == 200
    assert track_res_2.json()["analytics"]["conversions_a"] == 13
    assert float(track_res_2.json()["analytics"]["revenue"]) == 1000.50

    # 12. Soft-delete Campaign A
    delete_res = client.delete(
        f"/api/v1/campaigns/{campaign_a['id']}",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert delete_res.status_code == 204

    # Verify Campaign A is no longer accessible
    verify_delete = client.get(
        f"/api/v1/campaigns/{campaign_a['id']}",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert verify_delete.status_code == 404
