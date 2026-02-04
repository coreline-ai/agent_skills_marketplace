
"""Skills API."""

import uuid
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.common import Page
from app.schemas.skill import SkillDetail, SkillListItem, SkillQuery
from app.repos.skill_repo import SkillRepo

router = APIRouter()


@router.get("", response_model=Page[SkillListItem])
async def list_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    sort: str = "popularity",
    page: int = 1,
    size: int = 20,
):
    """List skills with filtering"""
    repo = SkillRepo(db)
    query = SkillQuery(
        q=q,
        category_slug=category,
        tag_slugs=tags,
        sort=sort,
        page=page,
        size=size
    )
    items, total = await repo.list_skills(query)
    
    total_pages = (total + size - 1) // size
    
    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=total_pages
    )


@router.get("/{id}", response_model=SkillDetail)
async def get_skill(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get skill details."""
    repo = SkillRepo(db)
    skill = await repo.get_skill(id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill
