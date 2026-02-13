"""Developer API (API-key protected)."""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_api_key, require_api_scope
from app.models.api_key import ApiKey
from app.repos.api_key_repo import ApiKeyRepo
from app.repos.public_filters import is_public_skill_url
from app.repos.skill_repo import SkillRepo
from app.schemas.api_key import ApiKeyUsagePoint, ApiKeyUsageResponse
from app.schemas.common import Page
from app.schemas.skill import SkillDetail, SkillListItem, SkillQuery

router = APIRouter()


@router.get("/skills", response_model=Page[SkillListItem])
async def developer_list_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[ApiKey, Depends(require_api_scope("read"))],
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Public skill list for external developers (API key required)."""
    _ = api_key
    repo = SkillRepo(db)
    query = SkillQuery(
        q=q,
        category_slug=category,
        tag_slugs=tags,
        sort=sort,
        page=page,
        size=size,
    )
    items, total = await repo.list_skills(query)
    pages = (total + size - 1) // size if total > 0 else 0
    return Page(items=items, total=int(total), page=page, size=size, pages=pages)


@router.get("/skills/{id}", response_model=SkillDetail)
async def developer_get_skill(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[ApiKey, Depends(require_api_scope("read"))],
):
    """Get a skill detail for developers (API key required)."""
    _ = api_key
    repo = SkillRepo(db)
    skill = await repo.get_skill(id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if not skill.is_official or not skill.is_verified or not is_public_skill_url(skill.url):
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/usage", response_model=ApiKeyUsageResponse)
async def developer_my_usage(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[ApiKey, Depends(require_api_key)],
):
    """Usage summary for the current API key."""
    repo = ApiKeyRepo(db)
    usage = await repo.get_usage_summary(api_key.id)
    return ApiKeyUsageResponse(
        api_key_id=api_key.id,
        today=usage["today"],
        this_month=usage["this_month"],
        daily=[
            ApiKeyUsagePoint(period=row.usage_date, request_count=int(row.request_count))
            for row in usage["daily"]
        ],
        monthly=[
            ApiKeyUsagePoint(period=row.usage_month, request_count=int(row.request_count))
            for row in usage["monthly"]
        ],
    )
