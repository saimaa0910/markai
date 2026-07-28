"""
EAIMOS CRM Interfaces
======================
Protocol declarations for Sprint 9 CRM services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.crm.dtos import (
    CreatePipelineDTO,
    PipelineResponseDTO,
    CreateDealDTO,
    DealResponseDTO,
    CreateLeadDTO,
    LeadResponseDTO,
)


class IPipelineService(Protocol):
    async def create_pipeline(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreatePipelineDTO
    ) -> ServiceResult[PipelineResponseDTO]: ...


class IDealService(Protocol):
    async def create_deal(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateDealDTO
    ) -> ServiceResult[DealResponseDTO]: ...


class ILeadQualificationService(Protocol):
    async def create_and_score_lead(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateLeadDTO
    ) -> ServiceResult[LeadResponseDTO]: ...
