"""Developer API key model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.api_key_usage import ApiKeyDailyUsage, ApiKeyMonthlyUsage, ApiKeyRateWindow


class ApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Hashed API keys for developer API access."""

    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String, nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    daily_usage: Mapped[list["ApiKeyDailyUsage"]] = relationship(
        "ApiKeyDailyUsage", back_populates="api_key", cascade="all, delete-orphan"
    )
    monthly_usage: Mapped[list["ApiKeyMonthlyUsage"]] = relationship(
        "ApiKeyMonthlyUsage", back_populates="api_key", cascade="all, delete-orphan"
    )
    rate_windows: Mapped[list["ApiKeyRateWindow"]] = relationship(
        "ApiKeyRateWindow", back_populates="api_key", cascade="all, delete-orphan"
    )

    @property
    def public_key_id(self) -> str:
        return f"{self.key_prefix}..."

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ApiKey {self.name} ({self.key_prefix})>"
