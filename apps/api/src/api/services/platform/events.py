"""
EAIMOS Platform Events
======================
Domain events for Sprint 6 Billing, Analytics & Security Platform.
"""

from api.services.base.events import DomainEvent


class SubscriptionCreated(DomainEvent):
    event_type: str = "billing.subscription_created"
    subscription_id: str = ""
    plan_tier: str = ""


class CreditsAdded(DomainEvent):
    event_type: str = "billing.credits_added"
    amount: float = 0.0


class SecurityIncidentReported(DomainEvent):
    event_type: str = "security.incident_reported"
    incident_id: str = ""
    severity: str = ""
