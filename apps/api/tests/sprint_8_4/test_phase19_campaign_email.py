"""Sprint 8.4 Phase 19: Campaign Broadcast Recipient Resolution

Acceptance criteria: campaign broadcast emails must be delivered to the
contact's email address. Previously the task passed ``contact.id`` as a
``user_id`` to the notification service, which looks up a ``User`` by that id
-- the contact was never found, so every campaign email was silently dropped.

Covers:
- Emails are sent to each contact's ``email`` column.
- Contacts without an email are skipped, and ``recipients_count`` reflects
  only actually-delivered recipients.
- The campaign is marked COMPLETED after the broadcast.
"""
import uuid
from contextlib import contextmanager

import pytest
from unittest.mock import patch

from api.database.session import SessionLocal
from api.models.campaign import Campaign, CampaignChannel, CampaignStatus
from api.models.contact import Contact
from api.models.organization import Organization
from api.worker.celery_app import campaign_broadcast_task


@contextmanager
def _fake_track_task_execution(*args, **kwargs):
    """Bypass telemetry/AlertEngine side effects in the worker."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fake_send(sent: dict):
    def _send(
        to_email, subject, html_body, template_name="custom",
        correlation_id=None, log_id=None,
    ):
        sent[to_email] = subject
        return True

    return _send


@pytest.mark.asyncio
async def test_campaign_broadcast_delivers_to_contact_email(db):
    import api.services.email_service as es

    org = Organization(name="Phase19 Org", slug=f"p19-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()

    contact_a = Contact(
        organization_id=org.id,
        first_name="Jane",
        last_name="Doe",
        email=f"jane-{uuid.uuid4().hex[:6]}@example.com",
    )
    contact_b = Contact(
        organization_id=org.id,
        first_name="Bob",
        last_name="Roe",
        email=f"bob-{uuid.uuid4().hex[:6]}@example.com",
    )
    contact_no_email = Contact(
        organization_id=org.id,
        first_name="No",
        last_name="Email",
        email="",
    )
    db.add_all([contact_a, contact_b, contact_no_email])

    campaign = Campaign(
        organization_id=org.id,
        title="March Newsletter",
        description="Spring update",
        channel=CampaignChannel.EMAIL,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    sent: dict = {}
    with patch(
        "api.worker.celery_app.track_task_execution",
        _fake_track_task_execution,
    ), patch.object(es, "_send_email", side_effect=_fake_send(sent)):
        result = campaign_broadcast_task.apply(
            args=[str(campaign.id)], throw=True
        )

    assert result.result["success"] is True
    assert result.result["recipients_count"] == 2
    assert contact_a.email in sent
    assert contact_b.email in sent
    assert contact_no_email.email not in sent
    assert sent[contact_a.email] == "March Newsletter"

    await db.refresh(campaign)
    assert campaign.status == CampaignStatus.COMPLETED
