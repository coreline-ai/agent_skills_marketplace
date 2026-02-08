"""Schemas for worker/runtime settings."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkerSettings(BaseModel):
    """Worker loop settings (admin-tunable)."""

    auto_ingest_enabled: bool = True
    auto_ingest_interval_seconds: int = Field(default=60, ge=10, le=86400)

    model_config = ConfigDict(extra="ignore")


class WorkerSettingsPatch(BaseModel):
    """Partial update payload for worker settings."""

    auto_ingest_enabled: Optional[bool] = None
    auto_ingest_interval_seconds: Optional[int] = Field(default=None, ge=10, le=86400)

    model_config = ConfigDict(extra="ignore")
