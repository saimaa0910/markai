import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.content_generator import GeneratedContent
from api.models.content_variant import ContentVariant
from api.services.llm import LLMGateway
from api.schemas.generator import (
    GeneratedContentCreate,
    GeneratedContentResponse,
    VariantRateRequest,
    ContentVariantResponse,
)

generator_router = APIRouter(prefix="/generator", tags=["content-generator"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@generator_router.post(
    "/", response_model=GeneratedContentResponse, status_code=status.HTTP_201_CREATED
)
def generate_copy(
    copy_in: GeneratedContentCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # 1. Compile prompt instruction
    keywords_str = (
        f" incorporating keywords: {copy_in.keywords}" if copy_in.keywords else ""
    )
    audience_str = f" tailored to: {copy_in.audience}" if copy_in.audience else ""

    prompt_used = (
        f"Create marketing {copy_in.copy_type} for '{copy_in.topic}'. "
        f"Tone: {copy_in.tone}.{audience_str}{keywords_str}"
    )

    # 2. Instantiate base record
    gen_content = GeneratedContent(
        title=copy_in.title,
        prompt_used=prompt_used,
        organization_id=membership.organization_id,
    )
    db.add(gen_content)
    db.flush()  # Extract ID prior to variants commit

    # 3. Call LLM Gateway to generate creative Variant A (Emotional hook style)
    prompt_a = f"{prompt_used}. Focus on an emotional hook or exciting narrative."
    content_a = LLMGateway.generate_response(
        prompt_content=prompt_a,
        model_name=copy_in.model_name,
    )
    # Append Variant A signature
    content_a = f"[Variant A - Creative Narrative]\n\n{content_a}"

    variant_a = ContentVariant(
        generated_content_id=gen_content.id,
        variant_label="Variant A",
        content=content_a,
        model_used=copy_in.model_name,
    )
    db.add(variant_a)

    # 4. Call LLM Gateway to generate conversion-driven Variant B (Concise benefits style)
    prompt_b = f"{prompt_used}. Focus on concise bullet points and a strong direct Call-To-Action (CTA)."
    content_b = LLMGateway.generate_response(
        prompt_content=prompt_b,
        model_name=copy_in.model_name,
    )
    # Append Variant B signature
    content_b = f"[Variant B - Direct CTA]\n\n{content_b}"

    variant_b = ContentVariant(
        generated_content_id=gen_content.id,
        variant_label="Variant B",
        content=content_b,
        model_used=copy_in.model_name,
    )
    db.add(variant_b)

    db.commit()
    db.refresh(gen_content)
    return gen_content


@generator_router.get("/", response_model=List[GeneratedContentResponse])
def list_generated_copies(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(GeneratedContent)
        .filter(GeneratedContent.organization_id == membership.organization_id)
        .all()
    )


@generator_router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generated_copy(
    content_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    gen = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.id == content_id,
            GeneratedContent.organization_id == membership.organization_id,
        )
        .first()
    )
    if not gen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated content record not found",
        )
    db.delete(gen)
    db.commit()


@generator_router.post(
    "/variants/{variant_id}/rate", response_model=ContentVariantResponse
)
def rate_variant(
    variant_id: uuid.UUID,
    rate_in: VariantRateRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Query variant and ensure user has tenant context access to the parent content
    variant = (
        db.query(ContentVariant)
        .join(GeneratedContent)
        .filter(
            ContentVariant.id == variant_id,
            GeneratedContent.organization_id == membership.organization_id,
        )
        .first()
    )
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content variant not found"
        )

    variant.rating = rate_in.rating
    db.commit()
    db.refresh(variant)
    return variant
