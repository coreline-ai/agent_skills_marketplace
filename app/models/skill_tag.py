"""Skill Tag association model."""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models._mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.tag import Tag


class SkillTag(Base, TimestampMixin):
    """Many-to-Many association between Skill and Tag."""

    __tablename__ = "skill_tags"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="tag_associations")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="skill_associations")

    def __repr__(self) -> str:
        return f"<SkillTag {self.skill_id}-{self.tag_id}>"
