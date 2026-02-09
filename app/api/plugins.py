"""Plugins API.

In this project, "Plugins" is a curated view over ingested SKILL.md items that
originate from plugin marketplace sources (e.g. Claude Code Marketplace).
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.ingest.sources import SOURCES
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


@router.get("", response_model=Page[SkillListItem])
async def list_plugins(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List plugin-marketplace items (as Skill cards) with filtering."""
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
    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=total_pages,
    )
