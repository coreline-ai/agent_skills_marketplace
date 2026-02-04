"""Category Alias model."""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category


class CategoryAlias(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Alias for mapping raw categories to normalized Categories."""

    __tablename__ = "category_aliases"

    alias: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<CategoryAlias {self.alias} -> {self.category_id}>"
