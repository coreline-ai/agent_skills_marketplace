"""Schemas for skill validation/enforcement settings."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SkillValidationSettings(BaseModel):
    """Runtime skill spec validation settings used by ingestion."""

    profile: Literal["lax", "strict"] = "lax"
    enforce: bool = False

    model_config = ConfigDict(extra="ignore")


class SkillValidationSettingsPatch(BaseModel):
    profile: Optional[Literal["lax", "strict"]] = None
    enforce: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")

