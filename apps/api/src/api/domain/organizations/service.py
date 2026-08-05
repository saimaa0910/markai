"""
Organizations Domain Service — Business Logic Delegation.
Delegates to existing Organization and UserOrganization models.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole


class OrganizationDomainService:
    def get_organization(self, db: Session, org_id: uuid.UUID) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id, Organization.deleted_at == None).first()

    def list_user_organizations(self, db: Session, user_id: uuid.UUID) -> List[Organization]:
        memberships = db.query(UserOrganization).filter(UserOrganization.user_id == user_id, UserOrganization.deleted_at == None).all()
        org_ids = [m.organization_id for m in memberships]
        return db.query(Organization).filter(Organization.id.in_(org_ids), Organization.deleted_at == None).all()

    def get_members(self, db: Session, org_id: uuid.UUID) -> List[UserOrganization]:
        return db.query(UserOrganization).filter(UserOrganization.organization_id == org_id, UserOrganization.deleted_at == None).all()


organization_domain_service = OrganizationDomainService()
