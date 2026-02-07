"""Skill Source Link model."""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.skill_source import SkillSource


class SkillSourceLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Link between a normalized Skill and its Source(s)."""

    __tablename__ = "skill_source_links"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_sources.id"), nullable=False
    )
    
    external_id: Mapped[str] = mapped_column(String, nullable=False) # e.g. URL specific to this skill in that source
    link_type: Mapped[str] = mapped_column(String, default="definition") # definition, reference, demo

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="source_links")
    source: Mapped["SkillSource"] = relationship("SkillSource")

    @property
    def url(self) -> str:
        """Expose a URL field for API schemas; default to external_id."""
        return self.external_id

    def __repr__(self) -> str:
        return f"<SkillSourceLink {self.skill_id}-{self.source_id}>"
