"""
EAIMOS CRM Dependencies
========================
FastAPI dependency providers for Sprint 9 CRM services.
"""

from api.services.base.dependency_provider import container
from api.services.crm.pipeline_service import PipelineService
from api.services.crm.deal_service import DealService
from api.services.crm.contact_management_service import ContactManagementService
from api.services.crm.lead_qualification_service import LeadQualificationService


def get_pipeline_service() -> PipelineService:
    return PipelineService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_deal_service() -> DealService:
    return DealService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_contact_management_service() -> ContactManagementService:
    return ContactManagementService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_lead_qualification_service() -> LeadQualificationService:
    return LeadQualificationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
