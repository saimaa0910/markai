"""
EAIMOS CRM Service Layer (Sprint 9)
=====================================
Public API for Pipelines, Deals, Contacts & AI Lead Qualification services.
"""

from api.services.crm.pipeline_service import PipelineService
from api.services.crm.deal_service import DealService
from api.services.crm.contact_management_service import ContactManagementService
from api.services.crm.lead_qualification_service import LeadQualificationService

from api.services.crm.dtos import (
    CreatePipelineDTO,
    PipelineResponseDTO,
    CreateDealDTO,
    DealResponseDTO,
    CreateLeadDTO,
    LeadResponseDTO,
)

from api.services.crm.events import (
    PipelineCreated,
    DealCreated,
    DealStageChanged,
    LeadQualified,
)

from api.services.crm.dependencies import (
    get_pipeline_service,
    get_deal_service,
    get_contact_management_service,
    get_lead_qualification_service,
)

__all__ = [
    "PipelineService",
    "DealService",
    "ContactManagementService",
    "LeadQualificationService",
    "CreatePipelineDTO",
    "PipelineResponseDTO",
    "CreateDealDTO",
    "DealResponseDTO",
    "CreateLeadDTO",
    "LeadResponseDTO",
    "get_pipeline_service",
    "get_deal_service",
    "get_contact_management_service",
    "get_lead_qualification_service",
]
