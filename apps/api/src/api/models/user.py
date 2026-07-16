from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.membership import UserOrganization


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    memberships: Mapped[List["UserOrganization"]] = relationship(
        "UserOrganization", back_populates="user", cascade="all, delete-orphan"
    )
