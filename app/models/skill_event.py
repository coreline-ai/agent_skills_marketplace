"""Skill Event model."""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill


class SkillEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Event log for skill interactions (view, use, favorite)."""

    __tablename__ = "skill_events"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String, nullable=False, index=True) # view, use, favorite
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Anonymous session ID
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # If we add user auth later
    
    # Context
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True) # e.g. "web", "api", "agent_x"
    context: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillEvent {self.type} on {self.skill_id}>"
