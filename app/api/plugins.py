"""Plugins API.

In this project, "Plugins" is a curated view over ingested SKILL.md items that
originate from plugin marketplace sources (e.g. Claude Code Marketplace).
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.cache_headers import PUBLIC_SEARCH_CACHE, REDIS_TTL_SEARCH, set_public_cache
from app.ingest.sources import SOURCES
from app.api.response_cache import set_cached_response, try_cached_response
from app.repos.skill_repo import SkillRepo
from app.schemas.common import Page
from app.schemas.skill import SkillListItem, SkillQuery

router = APIRouter()


def _default_plugin_source_names() -> list[str]:
    # SkillSource.name is persisted as the ingestion `source_id` string.
    names: set[str] = set()
    for source in SOURCES:
        sid = str(source.get("id", "")).strip()
        if not sid:
            continue
        group = str(source.get("group", "")).strip().lower()
        if group == "plugins":
            names.add(sid)

    # Backward compatible default.
    if not names:
        names.add("claude-code-marketplace-directory")
    return sorted(names)


def _skill_list_page_payload(page_result: Page[SkillListItem]) -> dict:
    return {
        "items": [SkillListItem.model_validate(item).model_dump(mode="json") for item in page_result.items],
        "total": page_result.total,
        "page": page_result.page,
        "size": page_result.size,
        "pages": page_result.pages,
    }


@router.get("", response_model=Page[SkillListItem])
async def list_plugins(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List plugin-marketplace items (as Skill cards) with filtering."""
    set_public_cache(response, PUBLIC_SEARCH_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="plugins:list",
        cache_control=PUBLIC_SEARCH_CACHE,
    )
    if cached is not None:
        return cached
    repo = SkillRepo(db)
    query = SkillQuery(
        q=q,
        category_slug=category,
        tag_slugs=tags,
        sort=sort,
        page=page,
        size=size,
    )
    items, total = await repo.list_skills_from_source_names(
        query,
        source_names=_default_plugin_source_names(),
    )
    total_pages = (total + size - 1) // size
    page_result = Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=total_pages,
    )
    payload = _skill_list_page_payload(page_result)
    await set_cached_response(
        request=request,
        namespace="plugins:list",
        payload=payload,
        ttl_seconds=REDIS_TTL_SEARCH,
    )
    response.headers["X-Cache"] = "MISS"
    return payload
