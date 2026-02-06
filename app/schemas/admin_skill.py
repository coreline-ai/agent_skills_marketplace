"""Admin Skill schemas."""

from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AdminSkillCreate(BaseModel):
    """Payload for creating/approving a skill."""
    slug: str
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    
    category_slug: Optional[str] = None # normalized category slug
    tags: list[str] = [] # normalized tag names

    # Content
    summary: Optional[str] = None
    content: Optional[str] = None
    
    # Interface
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    constraints: Optional[list[str]] = None
    triggers: Optional[list[str]] = None
    
    source_url: Optional[str] = None
    source_link: Optional[dict] = None # {source_id: UUID, external_id: str}
    is_official: bool = False
    is_verified: bool = False


class RawSkillReviewAction(BaseModel):
    action: str = "approve" # approve, reject
    
    # Overrides during approval
    slug: Optional[str] = None
    source_link: Optional[dict] = None # {source_id: UUID, external_id: str}


class AdminSkillUpdate(BaseModel):
    """Payload for updating a skill."""
    name: Optional[str] = None
    description: Optional[str] = None
    category_slug: Optional[str] = None
    tags: Optional[list[str]] = None
    
    summary: Optional[str] = None
    content: Optional[str] = None
    
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    constraints: Optional[list[str]] = None
    triggers: Optional[list[str]] = None
    
    is_official: Optional[bool] = None
    is_verified: Optional[bool] = None
