
"""Taxonomy API."""

from typing import Any, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.category import Category
from app.models.skill import Skill
from app.models.tag import Tag
from app.schemas.skill import CategoryWithCount, TagBase
from app.repos.public_filters import public_skill_conditions

router = APIRouter()

DEPRECATED_CATEGORY_SLUGS = {"chat", "code", "writing"}

async def _categories_payload(
    *,
    q: Optional[str],
    db: AsyncSession,
    skip: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Shared implementation for categories endpoints (keeps backward-compatible routes stable)."""
    stmt = select(Category).order_by(Category.display_order, Category.name)
    if q:
        stmt = stmt.where(Category.name.ilike(f"%{q}%"))
    stmt = stmt.offset(skip).limit(limit)

    categories = (await db.execute(stmt)).scalars().all()
    if not categories:
        return []
    categories = [c for c in categories if c.slug not in DEPRECATED_CATEGORY_SLUGS]
    if not categories:
        return []

    count_stmt = (
        select(Skill.category_id, func.count(Skill.id))
        .where(*public_skill_conditions(), Skill.category_id.is_not(None))
        .group_by(Skill.category_id)
    )
    count_rows = (await db.execute(count_stmt)).all()
    count_by_category_id = {row[0]: int(row[1]) for row in count_rows}

    return [
        {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "skill_count": count_by_category_id.get(category.id, 0),
        }
        for category in categories
    ]


@router.get("/categories", response_model=list[CategoryWithCount])
async def search_categories(
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all categories."""
    return await _categories_payload(q=q, db=db, skip=skip, limit=limit)


@router.get("/taxonomy/categories", response_model=list[CategoryWithCount])
async def search_categories_legacy(
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Backward-compatible alias for older clients."""
    return await _categories_payload(q=q, db=db, skip=skip, limit=limit)


@router.get("/tags", response_model=list[TagBase])
async def list_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
):
    """List tags (optional search)."""
    stmt = select(Tag).order_by(Tag.name).limit(100)
    if q:
        stmt = stmt.where(Tag.name.ilike(f"%{q}%"))
    
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/taxonomy/tags", response_model=list[TagBase])
async def list_tags_legacy(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
):
    """Backward-compatible alias for older clients."""
    return await list_tags(db=db, q=q)
