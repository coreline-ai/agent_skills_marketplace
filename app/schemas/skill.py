"""Skill schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CategoryWithCount(CategoryBase):
    skill_count: int = 0


class SkillSourceLinkBase(BaseModel):
    source_id: uuid.UUID
    external_id: str
    link_type: str
    url: Optional[str] = None # Computed in Repo
    model_config = ConfigDict(from_attributes=True)


class SkillBase(BaseModel):
    # Basic Info
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=120)

    # Popularity snapshot
    views: int = Field(default=0, ge=0)
    stars: int = Field(default=0, ge=0)
    score: float = Field(default=0.0, ge=0.0)

    is_official: bool = False
    description: Optional[str] = Field(None, max_length=1000)
    category_slug: Optional[str] = Field(None, max_length=50)
    tags: list[str] = Field(default_factory=list) # normalized tag names

    # Basic Content
    summary: Optional[str] = Field(None, max_length=2000)
    overview: Optional[str] = Field(None, max_length=10000)
    content: Optional[str] = Field(None, max_length=100000)
    author: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)

    # Interface
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    spec: Optional[dict[str, Any]] = None
    constraints: Optional[list[str]] = None
    triggers: Optional[list[str]] = None

    # New Fields
    github_stars: Optional[int] = None
    github_updated_at: Optional[datetime] = None
    use_cases: Optional[list[str]] = None
    quality_score: Optional[float] = None
    trust_score: Optional[float] = None
    trust_level: Optional[str] = None
    trust_flags: Optional[list[str]] = None
    trust_last_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Skill(SkillBase):
    id: UUID
    slug: str
    views: int = 0
    stars: int = 0
    score: float = 0.0
    created_at: datetime
    updated_at: datetime

    category: Optional[CategoryBase] = None
    tags: list[TagBase] = []
    source_links: list[SkillSourceLinkBase] = []

class SkillListItem(BaseModel):
    """Lightweight Skill representation for list endpoints."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    summary: Optional[str] = None
    views: int = 0
    stars: int = 0
    score: float = 0.0
    is_official: bool = False
    category_slug: Optional[str] = None
    category: Optional[CategoryBase] = None
    updated_at: datetime
    github_stars: Optional[int] = None
    github_updated_at: Optional[datetime] = None
    match_reason: Optional[str] = None
    quality_score: Optional[float] = None
    trust_score: Optional[float] = None
    trust_level: Optional[str] = None
    trust_flags: Optional[list[str]] = None
    trust_last_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SkillFilter(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None # category slug
    tags: Optional[list[str]] = None # list of tag slugs

class SkillQuery(BaseModel):
    q: Optional[str] = None
    category_slug: Optional[str] = None
    tag_slugs: Optional[list[str]] = None
    sort: str = "popularity"
    page: int = 1
    size: int = 20

SkillDetail = Skill
