"""Raw Skill model."""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill_source import SkillSource


class RawSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Raw skill data ingested from source (before normalization)."""

    __tablename__ = "raw_skills"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_sources.id"), nullable=False
    )
    
    # Raw Metadata
    external_id: Mapped[str] = mapped_column(String, nullable=False, index=True) # e.g. URL or Repo full_name
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Raw content (Markdown, JSON, etc.)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Parsing Status
    parse_status: Mapped[str] = mapped_column(String, default="pending", index=True) # pending, valid, error
    parse_error: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Parsed metadata/structure (if applicable)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    source: Mapped["SkillSource"] = relationship("SkillSource")

    def __repr__(self) -> str:
        return f"<RawSkill {self.external_id} ({self.parse_status})>"
