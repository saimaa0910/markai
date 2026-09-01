import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, ConfigDict
from api.models.integration import IntegrationProvider, IntegrationStatus


# --- INTEGRATION SCHEMAS ---

class IntegrationBase(BaseModel):
    provider: IntegrationProvider
    name: str
    config: Optional[Dict[str, Any]] = None


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[IntegrationStatus] = None


class IntegrationResponse(IntegrationBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: IntegrationStatus
    last_synced_at: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- CREDENTIAL SCHEMAS ---

class IntegrationCredentialUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[str] = None
    api_key: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


# --- SYNC JOB SCHEMAS ---

class SyncJobResponse(BaseModel):
    id: uuid.UUID
    integration_id: uuid.UUID
    organization_id: uuid.UUID
    status: str
    records_synced: int
    error_message: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)