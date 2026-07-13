from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_crm_multi_tenant_crud():
    """
    Verify CRM database models and routers support complete multi-tenant tenant isolation.
    """
    # 1. Register and login User A (creates Org A)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "superpassword123",
            "full_name": "User A",
            "org_name": "Org A",
        },
    )
    login_a = client.post(
        "/api/v1/auth/login",
        data={"username": "usera@example.com", "password": "superpassword123"},
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
            "email": "userb@example.com",
            "password": "superpassword123",
            "full_name": "User B",
            "org_name": "Org B",
        },
    )
    login_b = client.post(
        "/api/v1/auth/login",
        data={"username": "userb@example.com", "password": "superpassword123"},
    ).json()
    token_b = login_b["access_token"]

    # Retrieve Org B details
    orgs_b = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    org_b_id = orgs_b[0]["id"]

    # 3. Create Company under Org A
    comp_a_res = client.post(
        "/api/v1/crm/companies/",
        json={"name": "Company A", "domain": "compa.com"},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert comp_a_res.status_code == 201
    comp_a = comp_a_res.json()
    assert comp_a["name"] == "Company A"
    assert comp_a["organization_id"] == org_a_id

    # 4. Try listing companies under Org B (should be empty, verifying isolation)
    comps_b_res = client.get(
        "/api/v1/crm/companies/",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert comps_b_res.status_code == 200
    assert len(comps_b_res.json()) == 0

    # 5. Try querying Company A using Org B's token (should be blocked)
    comp_a_blocked = client.get(
        f"/api/v1/crm/companies/{comp_a['id']}",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    # User B is not part of Org A, so querying returns 404 Not Found to prevent data leakage
    assert comp_a_blocked.status_code == 404

    # 6. Create Contact under Org A linked to Company A
    contact_a_res = client.post(
        "/api/v1/crm/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@compa.com",
            "company_id": comp_a["id"],
        },
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert contact_a_res.status_code == 201
    contact_a = contact_a_res.json()
    assert contact_a["first_name"] == "John"
    assert contact_a["organization_id"] == org_a_id

    # 7. Create Lead under Org A
    lead_a_res = client.post(
        "/api/v1/crm/leads/",
        json={
            "title": "SaaS Deal A",
            "status": "NEW",
            "value": 15000.00,
            "contact_id": contact_a["id"],
            "company_id": comp_a["id"],
        },
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert lead_a_res.status_code == 201
    lead_a = lead_a_res.json()
    assert lead_a["title"] == "SaaS Deal A"
    assert float(lead_a["value"]) == 15000.00
