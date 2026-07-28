import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    ForeignKey, String, Text, Integer, Boolean, Float, JSON, DateTime,
    Table, Column, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

# Junction Table for Prompt <-> Tag (Many-to-Many)
prompt_tags_association = Table(
    "prompt_tags_association",
    Base.metadata,
    Column(
        "prompt_id",
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("prompt_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class PromptCollection(Base):
    __tablename__ = "prompt_collections"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="ORGANIZATION", nullable=False)  # ORGANIZATION, TEAM, PRIVATE, PUBLIC

    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", back_populates="collection", cascade="all, delete-orphan"
    )
    folders: Mapped[List["PromptFolder"]] = relationship(
        "PromptFolder", back_populates="collection", cascade="all, delete-orphan"
    )


class PromptFolder(Base):
    __tablename__ = "prompt_folders"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    collection: Mapped["PromptCollection"] = relationship("PromptCollection", back_populates="folders")
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", back_populates="folder"
    )


class PromptCategory(Base):
    __tablename__ = "prompt_categories"
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_prompt_category_name_org"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship("Prompt", back_populates="category_entity")


class PromptTag(Base):
    __tablename__ = "prompt_tags"
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_prompt_tag_name_org"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", secondary=prompt_tags_association, back_populates="tag_entities"
    )


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        Index("idx_prompts_org_name", "organization_id", "name"),
        Index("idx_prompts_org_status", "organization_id", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated list for backward compatibility
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="approved", nullable=False, index=True)  # draft, review, approved, production, archived
    change_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variable_specs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    visibility: Mapped[str] = mapped_column(String(50), default="organization", nullable=False)  # private, organization, public
    share_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    share_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    folder: Mapped[Optional["PromptFolder"]] = relationship("PromptFolder", back_populates="prompts")
    collection: Mapped[Optional["PromptCollection"]] = relationship("PromptCollection", back_populates="prompts")
    category_entity: Mapped[Optional["PromptCategory"]] = relationship("PromptCategory", back_populates="prompts")
    tag_entities: Mapped[List["PromptTag"]] = relationship(
        "PromptTag", secondary=prompt_tags_association, back_populates="prompts"
    )
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion", back_populates="prompt", cascade="all, delete-orphan"
    )
    variables: Mapped[List["PromptVariable"]] = relationship(
        "PromptVariable", back_populates="prompt", cascade="all, delete-orphan"
    )
    executions: Mapped[List["PromptExecution"]] = relationship(
        "PromptExecution", back_populates="prompt", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["PromptEvaluation"]] = relationship(
        "PromptEvaluation", back_populates="prompt", cascade="all, delete-orphan"
    )
    shares: Mapped[List["PromptShare"]] = relationship(
        "PromptShare", back_populates="prompt", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["PromptFavorite"]] = relationship(
        "PromptFavorite", back_populates="prompt", cascade="all, delete-orphan"
    )
    analytics: Mapped[Optional["PromptAnalytics"]] = relationship(
        "PromptAnalytics", back_populates="prompt", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["PromptAuditLog"]] = relationship(
        "PromptAuditLog", back_populates="prompt", cascade="all, delete-orphan"
    )
    comments: Mapped[List["PromptComment"]] = relationship(
        "PromptComment", back_populates="prompt", cascade="all, delete-orphan"
    )
    test_cases: Mapped[List["PromptTestCase"]] = relationship(
        "PromptTestCase", back_populates="prompt", cascade="all, delete-orphan"
    )

    @property
    def title(self) -> str:
        return self.name

    @title.setter
    def title(self, value: str) -> None:
        self.name = value

    @property
    def template(self) -> str:
        return self.content

    @template.setter
    def template(self, value: str) -> None:
        self.content = value

    @property
    def default_model(self) -> Optional[str]:
        return getattr(self, "_default_model", None)

    @default_model.setter
    def default_model(self, value: Optional[str]) -> None:
        self._default_model = value

    @property
    def default_provider(self) -> Optional[str]:
        return getattr(self, "_default_provider", None)

    @default_provider.setter
    def default_provider(self, value: Optional[str]) -> None:
        self._default_provider = value

    @property
    def temperature(self) -> float:
        return getattr(self, "_temperature", 0.7)

    @temperature.setter
    def temperature(self, value: float) -> None:
        self._temperature = value

    @property
    def top_p(self) -> float:
        return getattr(self, "_top_p", 1.0)

    @top_p.setter
    def top_p(self, value: float) -> None:
        self._top_p = value

    @property
    def max_tokens(self) -> Optional[int]:
        return getattr(self, "_max_tokens", None)

    @max_tokens.setter
    def max_tokens(self, value: Optional[int]) -> None:
        self._max_tokens = value

    @property
    def is_active(self) -> bool:
        return getattr(self, "_is_active", True)

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="uq_prompt_version_num"),
    )

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version_type: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)  # DRAFT, RELEASED, ARCHIVED
    content: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variable_specs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")
    variables: Mapped[List["PromptVariable"]] = relationship(
        "PromptVariable", back_populates="prompt_version", cascade="all, delete-orphan"
    )


class PromptVariable(Base):
    __tablename__ = "prompt_variables"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    variable_type: Mapped[str] = mapped_column(String(50), default="string", nullable=False)  # string, number, boolean, json, select
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="variables")
    prompt_version: Mapped[Optional["PromptVersion"]] = relationship("PromptVersion", back_populates="variables")


class PromptShare(Base):
    __tablename__ = "prompt_shares"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    share_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    visibility: Mapped[str] = mapped_column(String(50), default="organization", nullable=False)  # private, team, organization, public
    is_editable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shared_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="shares")


class PromptFavorite(Base):
    __tablename__ = "prompt_favorites"
    __table_args__ = (
        UniqueConstraint("prompt_id", "user_id", "organization_id", name="uq_prompt_fav_user_org"),
    )

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="favorites")


class PromptExecution(Base):
    __tablename__ = "prompt_executions"

    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    variables_used: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)  # success, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped[Optional["Prompt"]] = relationship("Prompt", back_populates="executions")


class PromptEvaluation(Base):
    __tablename__ = "prompt_evaluations"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    correctness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grounding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    safety_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="pass", nullable=False)  # pass, warning, fail
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="evaluations")
    test_case: Mapped["PromptTestCase"] = relationship("PromptTestCase", back_populates="evaluations")


class PromptAnalytics(Base):
    __tablename__ = "prompt_analytics"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="analytics")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="General", nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variable_specs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system_preset: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )


class PromptAuditLog(Base):
    __tablename__ = "prompt_audit_logs"

    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CREATED, UPDATED, DELETED, RESTORED, ARCHIVED, PURGED, CLONED, RELEASED, ROLLED_BACK, EXECUTED, SHARED, FAVORITED
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    prompt: Mapped[Optional["Prompt"]] = relationship("Prompt", back_populates="audit_logs")


class PromptComment(Base):
    __tablename__ = "prompt_comments"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="comments")


class PromptTestCase(Base):
    __tablename__ = "prompt_test_cases"

    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    prompt: Mapped[Optional["Prompt"]] = relationship("Prompt", back_populates="test_cases")
    evaluations: Mapped[List["PromptEvaluation"]] = relationship(
        "PromptEvaluation", back_populates="test_case", cascade="all, delete-orphan"
    )


class PromptRelease(Base):
    __tablename__ = "prompt_releases"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variable_specs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    release_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class PromptVersionHistory(Base):
    __tablename__ = "prompt_version_history"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DRAFT_CREATED, DRAFT_SAVED, RELEASED, ROLLBACK, CLONED, ARCHIVED
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
