import uuid
from typing import Optional, List
from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class PromptCollection(Base):
    __tablename__ = "prompt_collections"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="CASCADE"),
        nullable=False,
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
    )

    # Relationships
    collection: Mapped["PromptCollection"] = relationship("PromptCollection", back_populates="folders")
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", back_populates="folder"
    )


class Prompt(Base):
    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated list
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Extended Prompt Platform Columns
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="approved", nullable=False)  # draft, review, approved, production
    change_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    folder: Mapped[Optional["PromptFolder"]] = relationship("PromptFolder", back_populates="prompts")
    collection: Mapped[Optional["PromptCollection"]] = relationship("PromptCollection", back_populates="prompts")
    comments: Mapped[List["PromptComment"]] = relationship(
        "PromptComment", back_populates="prompt", cascade="all, delete-orphan"
    )
    test_cases: Mapped[List["PromptTestCase"]] = relationship(
        "PromptTestCase", back_populates="prompt", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["PromptEvaluation"]] = relationship(
        "PromptEvaluation", back_populates="prompt", cascade="all, delete-orphan"
    )


class PromptComment(Base):
    __tablename__ = "prompt_comments"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    prompt: Mapped[Optional["Prompt"]] = relationship("Prompt", back_populates="test_cases")
    evaluations: Mapped[List["PromptEvaluation"]] = relationship(
        "PromptEvaluation", back_populates="test_case", cascade="all, delete-orphan"
    )


class PromptEvaluation(Base):
    __tablename__ = "prompt_evaluations"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_test_cases.id", ondelete="CASCADE"),
        nullable=False,
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
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="evaluations")
    test_case: Mapped["PromptTestCase"] = relationship("PromptTestCase", back_populates="evaluations")


class PromptExecution(Base):
    __tablename__ = "prompt_executions"

    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
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
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
