import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt describing the desired image visual content.")
    style: Optional[str] = Field(None, description="Preset style (e.g. apple, minimal, glassmorphism).")
    aspect_ratio: Optional[str] = Field("1:1", description="Target layout ratio (1:1, 16:9, 9:16).")
    negative_prompt: Optional[str] = Field(None, description="Elements to exclude from the generation.")
    campaign_id: Optional[uuid.UUID] = Field(None, description="Optional Campaign ID mapping context.")
    knowledge_collections: Optional[List[uuid.UUID]] = Field(None, description="RAG collection ID filters.")
    model: Optional[str] = Field(None, description="Model tag override.")
    seed: Optional[int] = Field(None, description="PRNG Seed configuration.")
    steps: Optional[int] = Field(None, description="Iteration steps count.")
    cfg_scale: Optional[float] = Field(None, description="CFG scale prompt alignment strength.")


class ImageEditRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    prompt: str = Field(..., description="Detailed editing instructions.")
    mask_url: Optional[str] = Field(None, description="Base64 or URL mask overlays.")
    style: Optional[str] = Field(None, description="Style presets to apply.")
    model: Optional[str] = Field(None, description="Model tag to run.")


class ImageVariationRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    style: Optional[str] = Field(None, description="Style presets to apply.")
    model: Optional[str] = Field(None, description="Model tag to run.")


class ImageUpscaleRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    scale: Optional[float] = Field(2.0, description="Upscale multiplier (e.g. 2.0, 4.0).")


class ImageBackgroundRemoveRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")


class ImageBackgroundReplaceRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    background_prompt: str = Field(..., description="Prompt describing the new background.")


class ImageInpaintRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    mask_url: str = Field(..., description="Base64 or URL mask overlay.")
    prompt: str = Field(..., description="Object or detail to fill in mask.")


class ImageOutpaintRequest(BaseModel):
    image_url: str = Field(..., description="Source image URL.")
    mask_url: str = Field(..., description="Base64 or URL expansion mask.")
    prompt: str = Field(..., description="Visual scene descriptors to extend boundaries.")


class ImageResponse(BaseModel):
    id: str
    storage_url: str
    provider: str
    model: str
    prompt: str
    compiled_prompt: Optional[str] = None
    reflection: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None


class ImageLibraryItemResponse(BaseModel):
    id: uuid.UUID
    prompt: str
    negative_prompt: Optional[str] = None
    provider: str
    model: str
    seed: Optional[int] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    storage_url: str
    status: str
    version: int
    parent_id: Optional[uuid.UUID] = None
    tags: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: Any
    campaign_id: Optional[uuid.UUID] = None
    run_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ImageProviderResponse(BaseModel):
    name: str
    label: str
    priority: int
    configured: bool


class ImageModelResponse(BaseModel):
    name: str
    label: str
    provider: str
    supported_ratios: List[str]


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., max_length=255)


class CollectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    organization_id: uuid.UUID
    created_at: Any

    class Config:
        from_attributes = True


class BulkActionRequest(BaseModel):
    ids: List[uuid.UUID]
    target_collection_id: Optional[uuid.UUID] = None
