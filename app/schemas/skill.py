"""Skill schemas."""

import uuid
from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, ConfigDict


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
    name: str
    slug: str
    
    # Popularity snapshot
    views: int = 0
    stars: int = 0
    score: float = 0.0
    
    is_official: bool = False
    description: Optional[str] = None
    category_slug: Optional[str] = None # normalized category slug
    tags: list[str] = [] # normalized tag names

    # Basic Content
    summary: Optional[str] = None
    overview: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None # Computed in Repo

    # Interface
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    constraints: Optional[list[str]] = None
    triggers: Optional[list[str]] = None

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
SkillListItem = Skill
