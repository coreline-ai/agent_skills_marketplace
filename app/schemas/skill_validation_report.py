"""Schemas for validation dry-run reports."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SkillValidationReport(BaseModel):
    profile: Literal["lax", "strict"] = "strict"
    limit: int = Field(default=200, ge=1, le=5000)
    examined: int
    ok: int
    error: int
    top_errors: list[tuple[str, int]] = []

    model_config = ConfigDict(extra="ignore")

