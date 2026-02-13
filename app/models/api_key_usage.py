"""API key usage/rate window models."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.api_key import ApiKey


class ApiKeyRateWindow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-minute request counter for rate limiting."""

    __tablename__ = "api_key_rate_windows"
    __table_args__ = (
        UniqueConstraint("api_key_id", "window_start", name="uq_api_key_rate_windows_key_window"),
    )

    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True
    )
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    api_key: Mapped["ApiKey"] = relationship("ApiKey", back_populates="rate_windows")


class ApiKeyDailyUsage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Daily usage aggregate."""

    __tablename__ = "api_key_usage_daily"
    __table_args__ = (UniqueConstraint("api_key_id", "usage_date", name="uq_api_key_daily_key_date"),)

    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True
    )
    usage_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    api_key: Mapped["ApiKey"] = relationship("ApiKey", back_populates="daily_usage")


class ApiKeyMonthlyUsage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Monthly usage aggregate."""

    __tablename__ = "api_key_usage_monthly"
    __table_args__ = (
        UniqueConstraint("api_key_id", "usage_month", name="uq_api_key_monthly_key_month"),
    )

    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True
    )
    usage_month: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    api_key: Mapped["ApiKey"] = relationship("ApiKey", back_populates="monthly_usage")
