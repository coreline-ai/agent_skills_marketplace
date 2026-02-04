"""Skill Popularity model."""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models._mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill


class SkillPopularity(Base, TimestampMixin):
    """Aggregated popularity metrics for a skill."""

    __tablename__ = "skill_popularity"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )

    views: Mapped[int] = mapped_column(Integer, default=0)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True) # Calculated ranking score

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="popularity")

    def __repr__(self) -> str:
        return f"<SkillPopularity {self.skill_id}: {self.score}>"
