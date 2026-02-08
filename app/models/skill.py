
"""Skill model."""

import uuid
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.skill_tag import SkillTag
    from app.models.skill_popularity import SkillPopularity
    from app.models.skill_source_link import SkillSourceLink
    from app.models.tag import Tag


class Skill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Canonical Skill model."""

    __tablename__ = "skills"

    # Core Metadata
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)  # owner/name
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # A markdown overview intended for the detail page (LLM-generated).
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Canonical URL
    
    # Category
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    # Detailed Info
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Full structured content/readme
    
    # Interface Definitions (JSON)
    inputs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    outputs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Spec-aligned metadata (normalized Claude Skills frontmatter, etc.)
    spec: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Constraints/Depencencies
    constraints: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    triggers: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # Status
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="skills")
    tag_associations: Mapped[list["SkillTag"]] = relationship(
        "SkillTag", back_populates="skill", cascade="all, delete-orphan"
    )
    popularity: Mapped["SkillPopularity"] = relationship(
        "SkillPopularity", back_populates="skill", uselist=False, cascade="all, delete-orphan"
    )
    source_links: Mapped[list["SkillSourceLink"]] = relationship(
        "SkillSourceLink", back_populates="skill", cascade="all, delete-orphan"
    )

    @property
    def views(self) -> int:
        """Expose views from popularity relation for API schemas."""
        return self.popularity.views if self.popularity else 0

    @property
    def stars(self) -> int:
        """Expose favorites as stars for API schemas."""
        return self.popularity.favorites if self.popularity else 0

    @property
    def score(self) -> float:
        """Expose computed score from popularity relation."""
        return self.popularity.score if self.popularity else 0.0

    @property
    def tags(self) -> list["Tag"]:
        """Expose tags for API schemas (derived from SkillTag associations)."""
        tags: list["Tag"] = []
        for assoc in self.tag_associations or []:
            tag = getattr(assoc, "tag", None)
            if tag:
                tags.append(tag)
        return tags

    @property
    def category_slug(self) -> Optional[str]:
        """Expose category slug for API schemas."""
        if self.category:
            return getattr(self.category, "slug", None)
        return None

    def __repr__(self) -> str:
        return f"<Skill {self.slug}>"
