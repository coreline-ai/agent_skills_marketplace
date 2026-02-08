"""Skill pack schemas (group skills by repository)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PackListItem(BaseModel):
    """Repository-level grouping for public skills."""

    id: str  # url-safe repo id (owner__repo)
    repo_full_name: str  # owner/repo
    repo_url: str

    skill_count: int
    updated_at: datetime

    dotclaude_skill_count: int = 0
    skills_dir_skill_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PackDetail(PackListItem):
    """Pack detail metadata."""

    description: Optional[str] = None

