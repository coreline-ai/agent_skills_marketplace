"""Category model."""

from typing import TYPE_CHECKING
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.category_alias import CategoryAlias
    from app.models.skill import Skill


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Skill category (Normalized)."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    aliases: Mapped[list["CategoryAlias"]] = relationship(
        "CategoryAlias", back_populates="category", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship("Skill", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
