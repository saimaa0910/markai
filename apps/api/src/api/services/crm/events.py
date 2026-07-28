"""
EAIMOS CRM Domain Events
=========================
Domain events for Sprint 9 CRM & Sales Pipeline Services.
"""

from api.services.base.events import DomainEvent


class PipelineCreated(DomainEvent):
    event_type: str = "crm.pipeline_created"
    pipeline_id: str = ""
    name: str = ""


class DealCreated(DomainEvent):
    event_type: str = "crm.deal_created"
    deal_id: str = ""
    amount: float = 0.0


class DealStageChanged(DomainEvent):
    event_type: str = "crm.deal_stage_changed"
    deal_id: str = ""
    new_stage_id: str = ""


class LeadQualified(DomainEvent):
    event_type: str = "crm.lead_qualified"
    lead_id: str = ""
    score: int = 0
