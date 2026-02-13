
"""Taxonomy API."""

from typing import Any, Optional, Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.cache_headers import PUBLIC_TAXONOMY_CACHE, REDIS_TTL_TAXONOMY, set_public_cache
from app.models.category import Category
from app.models.skill import Skill
from app.models.tag import Tag
from app.schemas.skill import CategoryWithCount, TagBase
from app.repos.public_filters import public_skill_conditions
from app.api.response_cache import set_cached_response, try_cached_response

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
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "skill_count": count_by_category_id.get(category.id, 0),
        }
        for category in categories
    ]


@router.get("/categories", response_model=list[CategoryWithCount])
async def search_categories(
    request: Request,
    response: Response,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all categories."""
    set_public_cache(response, PUBLIC_TAXONOMY_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="taxonomy:categories",
        cache_control=PUBLIC_TAXONOMY_CACHE,
    )
    if cached is not None:
        return cached
    payload = await _categories_payload(q=q, db=db, skip=skip, limit=limit)
    await set_cached_response(
        request=request,
        namespace="taxonomy:categories",
        payload=payload,
        ttl_seconds=REDIS_TTL_TAXONOMY,
    )
    response.headers["X-Cache"] = "MISS"
    return payload


@router.get("/taxonomy/categories", response_model=list[CategoryWithCount])
async def search_categories_legacy(
    request: Request,
    response: Response,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Backward-compatible alias for older clients."""
    set_public_cache(response, PUBLIC_TAXONOMY_CACHE)
    return await search_categories(request=request, response=response, q=q, db=db, skip=skip, limit=limit)


@router.get("/tags", response_model=list[TagBase])
async def list_tags(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
):
    """List tags (optional search)."""
    set_public_cache(response, PUBLIC_TAXONOMY_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="taxonomy:tags",
        cache_control=PUBLIC_TAXONOMY_CACHE,
    )
    if cached is not None:
        return cached
    stmt = select(Tag).order_by(Tag.name).limit(100)
    if q:
        stmt = stmt.where(Tag.name.ilike(f"%{q}%"))

    result = await db.execute(stmt)
    tags = result.scalars().all()
    payload = [TagBase.model_validate(tag).model_dump(mode="json") for tag in tags]
    await set_cached_response(
        request=request,
        namespace="taxonomy:tags",
        payload=payload,
        ttl_seconds=REDIS_TTL_TAXONOMY,
    )
    response.headers["X-Cache"] = "MISS"
    return payload


@router.get("/taxonomy/tags", response_model=list[TagBase])
async def list_tags_legacy(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
):
    """Backward-compatible alias for older clients."""
    set_public_cache(response, PUBLIC_TAXONOMY_CACHE)
    return await list_tags(request=request, response=response, db=db, q=q)
