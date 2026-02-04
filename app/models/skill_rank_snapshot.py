"""Skill Rank Snapshot model."""

from sqlalchemy import Integer, Date, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class SkillRankSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Daily snapshot of skill rankings."""

    __tablename__ = "skill_rank_snapshots"

    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True, default=func.current_date())
    bucket: Mapped[str] = mapped_column(String, nullable=False, default="global") # global, category:slug
    
    # Ranked List
    rankings: Mapped[list[dict]] = mapped_column(JSONB, nullable=False) # list of {rank, skill_id, score, name, slug}

    def __repr__(self) -> str:
        return f"<SkillRankSnapshot {self.date} {self.bucket}>"
