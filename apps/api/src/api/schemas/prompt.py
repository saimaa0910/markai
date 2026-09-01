import uuid
import datetime
from typing import Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- CATEGORY SCHEMAS ---

class PromptCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class PromptCategoryCreate(PromptCategoryBase):
    pass


class PromptCategoryResponse(PromptCategoryBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- TAG SCHEMAS ---

class PromptTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = None


class PromptTagCreate(PromptTagBase):
    pass


class PromptTagResponse(PromptTagBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- COLLECTION & FOLDER SCHEMAS ---

class PromptCollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    visibility: Optional[str] = "ORGANIZATION"


class PromptCollectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_archived: bool = False
    is_favorite: bool = False
    is_pinned: bool = False
    visibility: str = "ORGANIZATION"
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class PromptFolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None


class PromptFolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

# --- PROMPT SCHEMAS ---

class PromptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    version: Optional[int] = 1
    category: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    tags: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_shared: Optional[bool] = True
    prompt_type: Optional[str] = "text"
    visibility: Optional[str] = "organization"


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    tags: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_shared: Optional[bool] = None
    status: Optional[str] = None
    change_log: Optional[str] = None
    prompt_type: Optional[str] = None
    visibility: Optional[str] = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    content: str
    version: Optional[int] = 1
    category: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    is_shared: Optional[bool] = True
    organization_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = False
    is_favorite: Optional[bool] = False
    is_pinned: Optional[bool] = False
    status: Optional[str] = "approved"
    prompt_type: Optional[str] = "text"
    change_log: Optional[str] = None
    variable_specs: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PromptVersionResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    version_number: int
    version_type: str
    content: str
    system_prompt: Optional[str] = None
    variable_specs: Optional[Dict[str, Any]] = None
    changelog: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class PromptExecuteRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[int] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    rag_enabled: Optional[bool] = False
    temperature: Optional[float] = 0.7


class PromptExecuteResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    prompt_name: str
    prompt_version: int
    provider: str
    model: str
    output: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    tokens_used: int
    cost_usd: float
    status: str = "success"
    error_message: Optional[str] = None


class PromptOptimizeRequest(BaseModel):
    content: str


class PromptImportRequest(BaseModel):
    file_content: str
    format_type: str = "json"  # json, csv, yaml


class PromptShareRequest(BaseModel):
    visibility: str = "organization"  # private, organization, public
    expires_in_days: Optional[int] = None
    is_editable: Optional[bool] = False


class PromptShareResponse(BaseModel):
    share_token: str
    share_url: str
    visibility: str
    expires_at: Optional[str] = None
    is_editable: bool


class PromptBulkActionRequest(BaseModel):
    action: str  # archive, restore, delete, permanent_delete, tag
    prompt_names: List[str]
    payload: Optional[Dict[str, Any]] = None


class PromptSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    tag: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    collection_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = False
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    skip: Optional[int] = 0
    limit: Optional[int] = 50
    sort_by: Optional[str] = "updated_at"
    sort_order: Optional[str] = "desc"


class PromptTestCaseCreate(BaseModel):
    name: str
    inputs: dict
    expected_output: Optional[str] = None


class PromptTestCaseResponse(BaseModel):
    id: uuid.UUID
    prompt_id: Optional[uuid.UUID] = None
    name: str
    inputs: dict
    expected_output: Optional[str] = None
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class PromptEvaluationResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    test_case_id: uuid.UUID
    model_name: str
    actual_output: Optional[str] = None
    correctness_score: Optional[float] = None
    grounding_score: Optional[float] = None
    relevance_score: Optional[float] = None
    consistency_score: Optional[float] = None
    safety_score: Optional[float] = None
    hallucination_risk: Optional[float] = None
    overall_score: Optional[float] = None
    status: str
    latency_ms: int
    cost_usd: float
    tokens_used: int

    model_config = ConfigDict(from_attributes=True)

class PromptAnalyticsResponse(BaseModel):
    total_prompts: int
    total_executions: int
    avg_latency_ms: float
    avg_cost_usd: float
    success_rate: float
    categories_breakdown: List[Dict[str, Any]]
    daily_executions: List[Dict[str, Any]]


class PromptAuditLogResponse(BaseModel):
    id: uuid.UUID
    prompt_id: Optional[uuid.UUID] = None
    prompt_name: str
    action: str
    user_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)