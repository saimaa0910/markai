import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.company import Company
from api.models.contact import Contact
from api.models.lead import Lead
from api.models.activity import Activity
from api.schemas.crm import (
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
    CompanyCreate,
    CompanyResponse,
    ContactCreate,
    ContactResponse,
    LeadCreate,
    LeadResponse,
    LeadUpdate,
    ActivityCreate,
    ActivityResponse,
)

# APIRouters for separate sub-resources
companies_router = APIRouter(prefix="/crm/companies", tags=["crm-companies"])
contacts_router = APIRouter(prefix="/crm/contacts", tags=["crm-contacts"])
leads_router = APIRouter(prefix="/crm/leads", tags=["crm-leads"])
activities_router = APIRouter(prefix="/crm/activities", tags=["crm-activities"])

# Enforce MEMBER permissions on CRM routes
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# ==========================================
# COMPANIES ENDPOINTS
# ==========================================


@companies_router.post(
    "/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED
)
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    company = Company(
        name=company_in.name,
        domain=company_in.domain,
        industry=company_in.industry,
        size=company_in.size,
        organization_id=membership.organization_id,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@companies_router.get("/", response_model=List[CompanyResponse])
def list_companies(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(Company)
        .filter(Company.organization_id == membership.organization_id)
        .all()
    )


@companies_router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    company = (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.organization_id == membership.organization_id,
        )
        .first()
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@companies_router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    company = (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.organization_id == membership.organization_id,
        )
        .first()
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    db.delete(company)
    db.commit()


# ==========================================
# CONTACTS ENDPOINTS
# ==========================================


@contacts_router.post(
    "/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED
)
def create_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify company belongs to organization if provided
    if contact_in.company_id:
        company = (
            db.query(Company)
            .filter(
                Company.id == contact_in.company_id,
                Company.organization_id == membership.organization_id,
            )
            .first()
        )
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided company does not exist in this organization",
            )

    contact = Contact(
        first_name=contact_in.first_name,
        last_name=contact_in.last_name,
        email=contact_in.email,
        phone=contact_in.phone,
        job_title=contact_in.job_title,
        company_id=contact_in.company_id,
        organization_id=membership.organization_id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@contacts_router.get("/", response_model=List[ContactResponse])
def list_contacts(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(Contact)
        .filter(Contact.organization_id == membership.organization_id)
        .all()
    )


@contacts_router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.organization_id == membership.organization_id,
        )
        .first()
    )
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    db.delete(contact)
    db.commit()


# ==========================================
# LEADS ENDPOINTS
# ==========================================


@leads_router.post(
    "/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED
)
def create_lead(
    lead_in: LeadCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify contact relationship
    if lead_in.contact_id:
        contact = (
            db.query(Contact)
            .filter(
                Contact.id == lead_in.contact_id,
                Contact.organization_id == membership.organization_id,
            )
            .first()
        )
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided contact does not exist in this organization",
            )

    lead = Lead(
        title=lead_in.title,
        status=lead_in.status,
        value=lead_in.value or 0.00,
        contact_id=lead_in.contact_id,
        company_id=lead_in.company_id,
        organization_id=membership.organization_id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@leads_router.get("/", response_model=List[LeadResponse])
def list_leads(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(Lead).filter(Lead.organization_id == membership.organization_id).all()
    )


@leads_router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.organization_id == membership.organization_id)
        .first()
    )
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )
    db.delete(lead)
    db.commit()


@leads_router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: uuid.UUID,
    lead_in: LeadUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.organization_id == membership.organization_id)
        .first()
    )
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    # Apply updates
    update_data = lead_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(lead, field, val)

    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


# ==========================================
# ACTIVITIES ENDPOINTS
# ==========================================


@activities_router.post(
    "/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED
)
def create_activity(
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify relationship linkages
    if activity_in.lead_id:
        lead = (
            db.query(Lead)
            .filter(
                Lead.id == activity_in.lead_id,
                Lead.organization_id == membership.organization_id,
            )
            .first()
        )
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided lead does not exist in this organization",
            )

    activity = Activity(
        type=activity_in.type,
        title=activity_in.title,
        description=activity_in.description,
        lead_id=activity_in.lead_id,
        contact_id=activity_in.contact_id,
        organization_id=membership.organization_id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@activities_router.get("/", response_model=List[ActivityResponse])
def list_activities(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(Activity)
        .filter(Activity.organization_id == membership.organization_id)
        .all()
    )
