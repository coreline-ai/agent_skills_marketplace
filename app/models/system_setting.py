"""System settings model (runtime-tunable configuration stored in DB)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Key-value settings row.

    We intentionally keep this generic (JSON value) so we can add admin-tunable
    toggles without schema churn.
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SystemSetting {self.key}>"

