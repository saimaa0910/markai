"""
Domain Entity Base Classes & Value Objects.
"""

from typing import Optional
import uuid
import datetime
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """
    Domain Entity Base Contract.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    class Config:
        arbitrary_types_allowed = True
