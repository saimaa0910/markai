"""
CRM Domain Service — Business Logic Delegation.
Delegates to existing CRM models and repositories.
"""

from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from api.models.contact import Contact
from api.models.company import Company
from api.models.lead import Lead
from api.models.activity import Activity


class CRMService:
    def get_contacts(self, db: Session, org_id: uuid.UUID) -> List[Contact]:
        return db.query(Contact).filter(Contact.organization_id == org_id).all()

    def get_companies(self, db: Session, org_id: uuid.UUID) -> List[Company]:
        return db.query(Company).filter(Company.organization_id == org_id).all()

    def get_leads(self, db: Session, org_id: uuid.UUID) -> List[Lead]:
        return db.query(Lead).filter(Lead.organization_id == org_id).all()

    def get_activities(self, db: Session, org_id: uuid.UUID) -> List[Activity]:
        return db.query(Activity).filter(Activity.organization_id == org_id).all()


crm_service = CRMService()
