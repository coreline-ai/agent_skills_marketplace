"""GitHub Repo Cache model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class GithubRepoCache(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cache for GitHub API responses to built rate limits."""

    __tablename__ = "github_repo_cache"

    repo_url: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    etag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_modified: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Data
    data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True) # Cached API response
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<GithubRepoCache {self.repo_url}>"
