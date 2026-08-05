"""
Billing Domain Service — Business Logic Delegation.
Delegates to existing Billing models & database session.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from api.models.billing import BillingPlan, Subscription, Invoice, Credit


class BillingDomainService:
    def get_subscription(self, db: Session, org_id: uuid.UUID) -> Optional[Subscription]:
        return db.query(Subscription).filter(Subscription.organization_id == org_id, Subscription.deleted_at == None).first()

    def list_plans(self, db: Session) -> List[BillingPlan]:
        return db.query(BillingPlan).filter(BillingPlan.is_active == True, BillingPlan.deleted_at == None).all()

    def get_invoices(self, db: Session, org_id: uuid.UUID) -> List[Invoice]:
        return db.query(Invoice).filter(Invoice.organization_id == org_id, Invoice.deleted_at == None).all()

    def get_credits(self, db: Session, org_id: uuid.UUID) -> Optional[Credit]:
        return db.query(Credit).filter(Credit.organization_id == org_id, Credit.deleted_at == None).first()


billing_domain_service = BillingDomainService()
