"""
Pytest Test Suite — Multi-Sprint Verification (Sprints 2–15)
===========================================================
Verifies repository operations across all domain platforms:
IAM, AI Gateway, Prompts, Knowledge, AI Agents, Workflows, Marketing, CRM, Integrations, Notifications, Billing, Analytics, Security, Administration.
"""

import asyncio
import datetime
import uuid
import pytest

from api.repositories import (
    OrganizationRepository,
    UserRepository,
    APIKeyRepository,
    AIProviderRepository,
    EnterprisePromptRepository,
    KnowledgeDocumentRepository,
    EnterpriseAgentDefinitionRepository,
    WorkflowDefinitionRepository,
    EnterpriseCampaignRepository,
    CompanyRepository,
    IntegrationRepository,
    NotificationRepository,
    BillingPlanRepository,
    AnalyticsDashboardRepository,
    SecurityIncidentRepository,
    SupportTicketRepository,
)


def run_async(coro):
    return asyncio.run(coro)


def test_sprint_2_iam_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        user_repo = UserRepository()
        org = await org_repo.create(db_session, {"name": "IAM Test Org", "slug": f"iam-{uuid.uuid4().hex[:6]}"})
        user = await user_repo.create(db_session, {
            "email": f"iam_user_{uuid.uuid4().hex[:6]}@example.com",
            "hashed_password": "secret_password",
            "full_name": "IAM User",
            "first_name": "IAM",
            "last_name": "User",
        })

        api_key_repo = APIKeyRepository(organization_id=org.id)
        key = await api_key_repo.create(db_session, {
            "user_id": user.id,
            "name": "Production Key",
            "key_hash": f"hash_{uuid.uuid4().hex}",
            "key_prefix": "eai_",
        })
        assert key.id is not None
        assert key.organization_id == org.id

    run_async(_test())


def test_sprint_3_ai_gateway_repository(db_session):
    async def _test():
        provider_repo = AIProviderRepository()
        provider = await provider_repo.create(db_session, {
            "name": f"OpenAI_{uuid.uuid4().hex[:6]}",
        })
        assert provider.id is not None

        fetched = await provider_repo.get_by_code(db_session, provider.name)
        assert fetched is not None
        assert fetched.id == provider.id

    run_async(_test())


def test_sprint_4_prompt_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Prompt Org", "slug": f"prompt-{uuid.uuid4().hex[:6]}"})

        prompt_repo = EnterprisePromptRepository(organization_id=org.id)
        prompt = await prompt_repo.create(db_session, {
            "name": "Customer Support Prompt",
            "content": "You are a helpful customer assistant.",
        })
        assert prompt.id is not None
        assert prompt.organization_id == org.id

    run_async(_test())


def test_sprint_5_knowledge_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Knowledge Org", "slug": f"know-{uuid.uuid4().hex[:6]}"})

        doc_repo = KnowledgeDocumentRepository(organization_id=org.id)
        doc = await doc_repo.create(db_session, {
            "title": "EAIMOS Architecture Spec",
            "file_type": "pdf",
        })
        assert doc.id is not None
        assert doc.organization_id == org.id

    run_async(_test())


def test_sprint_6_agents_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Agents Org", "slug": f"agent-{uuid.uuid4().hex[:6]}"})

        agent_repo = EnterpriseAgentDefinitionRepository(organization_id=org.id)
        agent = await agent_repo.create(db_session, {
            "name": f"Copywriter Agent {uuid.uuid4().hex[:4]}",
            "system_prompt": "You write engaging marketing emails.",
        })
        assert agent.id is not None

    run_async(_test())


def test_sprint_7_workflow_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Workflow Org", "slug": f"wf-{uuid.uuid4().hex[:6]}"})

        wf_repo = WorkflowDefinitionRepository(organization_id=org.id)
        wf = await wf_repo.create(db_session, {
            "name": "Lead Enrichment Pipeline",
            "steps_definition": {"steps": []},
        })
        assert wf.id is not None

    run_async(_test())


def test_sprint_8_marketing_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Marketing Org", "slug": f"mkt-{uuid.uuid4().hex[:6]}"})

        camp_repo = EnterpriseCampaignRepository(organization_id=org.id)
        camp = await camp_repo.create(db_session, {
            "title": "Summer Product Launch",
            "channel": "EMAIL",
        })
        assert camp.id is not None

    run_async(_test())


def test_sprint_9_crm_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "CRM Org", "slug": f"crm-{uuid.uuid4().hex[:6]}"})

        comp_repo = CompanyRepository(organization_id=org.id)
        comp = await comp_repo.create(db_session, {
            "name": "Stark Industries",
            "domain": f"stark-{uuid.uuid4().hex[:4]}.com",
        })
        assert comp.id is not None

    run_async(_test())


def test_sprint_10_integrations_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Integ Org", "slug": f"integ-{uuid.uuid4().hex[:6]}"})

        integ_repo = IntegrationRepository(organization_id=org.id)
        integ = await integ_repo.create(db_session, {
            "name": "HubSpot Sync",
            "provider": f"hubspot_{uuid.uuid4().hex[:4]}",
        })
        assert integ.id is not None

    run_async(_test())


def test_sprint_11_notifications_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        user_repo = UserRepository()
        org = await org_repo.create(db_session, {"name": "Notif Org", "slug": f"notif-{uuid.uuid4().hex[:6]}"})
        user = await user_repo.create(db_session, {
            "email": f"notif_user_{uuid.uuid4().hex[:6]}@example.com",
            "hashed_password": "secret_password",
            "full_name": "Notif User",
            "first_name": "Notif",
            "last_name": "User",
        })

        notif_repo = NotificationRepository(organization_id=org.id)
        notif = await notif_repo.create(db_session, {
            "user_id": user.id,
            "title": "Welcome to EAIMOS",
            "body": "Your account is activated.",
        })
        assert notif.id is not None

    run_async(_test())


def test_sprint_12_billing_repository(db_session):
    async def _test():
        plan_repo = BillingPlanRepository()
        plan = await plan_repo.create(db_session, {
            "name": "Enterprise Pro",
            "slug": f"pro_{uuid.uuid4().hex[:6]}",
            "tier": "enterprise",
            "billing_cycle": "monthly",
        })
        assert plan.id is not None

    run_async(_test())


def test_sprint_13_analytics_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Analytics Org", "slug": f"analytics-{uuid.uuid4().hex[:6]}"})

        dash_repo = AnalyticsDashboardRepository(organization_id=org.id)
        dash = await dash_repo.create(db_session, {
            "name": "Executive Marketing Overview",
        })
        assert dash.id is not None

    run_async(_test())


def test_sprint_14_security_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        org = await org_repo.create(db_session, {"name": "Security Org", "slug": f"sec-{uuid.uuid4().hex[:6]}"})

        inc_repo = SecurityIncidentRepository(organization_id=org.id)
        inc = await inc_repo.create(db_session, {
            "title": "Suspicious Login Spike",
            "description": "High volume of login attempts from new IP",
            "category": "AUTHENTICATION",
            "detected_at": datetime.datetime.now(datetime.timezone.utc),
        })
        assert inc.id is not None

    run_async(_test())


def test_sprint_15_admin_repository(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        user_repo = UserRepository()
        org = await org_repo.create(db_session, {"name": "Admin Org", "slug": f"admin-{uuid.uuid4().hex[:6]}"})
        user = await user_repo.create(db_session, {
            "email": f"admin_user_{uuid.uuid4().hex[:6]}@example.com",
            "hashed_password": "secret_password",
            "full_name": "Admin User",
            "first_name": "Admin",
            "last_name": "User",
        })

        ticket_repo = SupportTicketRepository(organization_id=org.id)
        ticket = await ticket_repo.create(db_session, {
            "created_by": user.id,
            "ticket_number": f"TICK-{uuid.uuid4().hex[:6].upper()}",
            "title": "API Rate Limit Query",
            "description": "Request to increase rate limit for production batch job.",
        })
        assert ticket.id is not None

    run_async(_test())
