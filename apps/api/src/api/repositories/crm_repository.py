"""
EAIMOS CRM Repository Module — Sprint 9
=======================================
Repository implementations for CRM models:
Company, Contact, Lead, Activity, Deal.
"""

from typing import Any, List, Optional
import uuid

from api.models.company import Company
from api.models.contact import Contact
from api.models.lead import Lead
from api.models.activity import Activity
from api.models.deals import Deal
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class CompanyRepository(TenantRepository[Company]):
    """Data access layer for CRM Companies."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Company, organization_id=organization_id)

    async def get_by_domain(self, session: Any, domain: str) -> Optional[Company]:
        filters = [FilterParam(field="domain", operator=FilterOperator.EQ, value=domain)]
        return await self.find_one(session=session, filters=filters)


class ContactRepository(TenantRepository[Contact]):
    """Data access layer for CRM Contacts."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Contact, organization_id=organization_id)

    async def get_by_email(self, session: Any, email: str) -> Optional[Contact]:
        filters = [FilterParam(field="email", operator=FilterOperator.EQ, value=email.lower())]
        return await self.find_one(session=session, filters=filters)


class LeadRepository(TenantRepository[Lead]):
    """Data access layer for CRM Leads."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Lead, organization_id=organization_id)


class ActivityRepository(TenantRepository[Activity]):
    """Data access layer for CRM Activities."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Activity, organization_id=organization_id)


class DealRepository(TenantRepository[Deal]):
    """Data access layer for CRM Pipeline Deals."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Deal, organization_id=organization_id)
