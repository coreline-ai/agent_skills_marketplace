
"""Taxonomy API."""

from typing import Any, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.skill import CategoryBase, TagBase

router = APIRouter()


@router.get("/categories", response_model=list[CategoryBase])
async def search_categories(
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all categories."""
    stmt = select(Category).order_by(Category.display_order, Category.name)
    if q:
        stmt = stmt.where(Category.name.ilike(f"%{q}%"))
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tags", response_model=list[TagBase])
async def list_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
):
    """List tags (optional search)."""
    stmt = select(Tag).order_by(Tag.name).limit(100)
    if q:
        stmt = stmt.where(Tag.name.ilike(f"%{q}%"))
    
    result = await db.execute(stmt)
    return result.scalars().all()
