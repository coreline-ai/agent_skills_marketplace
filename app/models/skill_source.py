"""Skill Source model."""

from typing import Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class SkillSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Source of skills (e.g., GitHub repository, Awesome list)."""

    __tablename__ = "skill_sources"

    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # github_repo, awesome_list, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillSource {self.name}>"
