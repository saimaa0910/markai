import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# --- GENERATOR SCHEMAS ---


class GeneratedContentCreate(BaseModel):
    title: str = Field(..., max_length=255)
    copy_type: str = "social"  # 'social', 'email', 'ad'
    topic: str
    tone: str = "professional"  # 'professional', 'creative', 'witty'
    audience: Optional[str] = None
    keywords: Optional[str] = None
    model_name: str = "gemini-1.5-flash"


class ContentVariantResponse(BaseModel):
    id: uuid.UUID
    generated_content_id: uuid.UUID
    variant_label: str
    content: str
    model_used: str
    rating: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class GeneratedContentResponse(BaseModel):
    id: uuid.UUID
    title: str
    prompt_used: str
    organization_id: uuid.UUID
    variants: List[ContentVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- VARIANT RATING SCHEMA ---


class VariantRateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
