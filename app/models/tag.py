"""Tag model."""

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill_tag import SkillTag


class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Skill tag (Normalized in lower-kebab-case)."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

    # Relationships
    skill_associations: Mapped[list["SkillTag"]] = relationship("SkillTag", back_populates="tag")

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
