"""Packs API (group public skills by repository)."""

from __future__ import annotations

import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.skill import Skill
from app.repos.public_filters import public_skill_conditions
from app.schemas.common import Page
from app.schemas.pack import PackListItem, PackDetail
from app.schemas.skill import SkillListItem

router = APIRouter()

_REPO_FULL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _pack_id_from_repo_full_name(repo_full_name: str) -> str:
    return repo_full_name.replace("/", "__")


def _repo_full_name_from_pack_id(pack_id: str) -> str:
    repo_full_name = (pack_id or "").strip().replace("__", "/")
    if not _REPO_FULL_NAME_RE.match(repo_full_name):
        raise HTTPException(status_code=404, detail="Pack not found")
    return repo_full_name


def _repo_full_name_expr():
    """
    Extract owner/repo from canonical GitHub skill doc URL.
    We only query rows passing `public_skill_conditions()`, so URL format is stable.
    """
    p = func.split_part(Skill.url, "https://github.com/", 2)
    owner = func.split_part(p, "/", 1)
    repo = func.split_part(p, "/", 2)
    return func.concat(owner, literal("/"), repo)


def _repo_url_expr(repo_full_name):
    return func.concat(literal("https://github.com/"), repo_full_name)


@router.get("", response_model=Page[PackListItem])
async def list_packs(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
    sort: str = "skills",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    repo_full_name = _repo_full_name_expr().label("repo_full_name")
    repo_url = _repo_url_expr(repo_full_name).label("repo_url")

    dotclaude_count = func.sum(
        case((Skill.url.ilike("%/.claude/skills/%/SKILL.md"), 1), else_=0)
    ).label("dotclaude_skill_count")
    skills_dir_count = func.sum(
        case((Skill.url.ilike("%/skills/%/SKILL.md"), 1), else_=0)
    ).label("skills_dir_skill_count")

    base = (
        select(
            repo_full_name,
            repo_url,
            func.count(Skill.id).label("skill_count"),
            func.max(Skill.updated_at).label("updated_at"),
            dotclaude_count,
            skills_dir_count,
        )
        .where(*public_skill_conditions())
        .group_by(repo_full_name, repo_url)
    )

    if q:
        needle = q.strip()
        if needle:
            base = base.having(repo_full_name.ilike(f"%{needle}%"))

    # Count total packs
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    # Sorting
    if sort == "updated":
        base = base.order_by(desc(func.max(Skill.updated_at)))
    else:
        # Default: by number of skills, then by recency
        base = base.order_by(desc(func.count(Skill.id)), desc(func.max(Skill.updated_at)))

    base = base.offset((page - 1) * size).limit(size)
    rows = (await db.execute(base)).all()

    items: list[PackListItem] = []
    for row in rows:
        repo_full_name_value = str(row.repo_full_name)
        items.append(
            PackListItem(
                id=_pack_id_from_repo_full_name(repo_full_name_value),
                repo_full_name=repo_full_name_value,
                repo_url=str(row.repo_url),
                skill_count=int(row.skill_count or 0),
                updated_at=row.updated_at,
                dotclaude_skill_count=int(row.dotclaude_skill_count or 0),
                skills_dir_skill_count=int(row.skills_dir_skill_count or 0),
            )
        )

    pages = (int(total or 0) + size - 1) // size
    return Page(items=items, total=int(total or 0), page=page, size=size, pages=pages)


@router.get("/{id}", response_model=PackDetail)
async def get_pack(
    id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo_full_name_value = _repo_full_name_from_pack_id(id)
    repo_full_name = _repo_full_name_expr().label("repo_full_name")
    repo_url = _repo_url_expr(repo_full_name).label("repo_url")

    dotclaude_count = func.sum(
        case((Skill.url.ilike("%/.claude/skills/%/SKILL.md"), 1), else_=0)
    ).label("dotclaude_skill_count")
    skills_dir_count = func.sum(
        case((Skill.url.ilike("%/skills/%/SKILL.md"), 1), else_=0)
    ).label("skills_dir_skill_count")

    stmt = (
        select(
            repo_full_name,
            repo_url,
            func.count(Skill.id).label("skill_count"),
            func.max(Skill.updated_at).label("updated_at"),
            dotclaude_count,
            skills_dir_count,
        )
        .where(*public_skill_conditions())
        .group_by(repo_full_name, repo_url)
        .having(repo_full_name == repo_full_name_value)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pack not found")

    # Optional description: use the most recently updated skill description as a placeholder.
    desc_stmt = (
        select(Skill.description)
        .where(*public_skill_conditions())
        .where(repo_full_name == repo_full_name_value)
        .order_by(Skill.updated_at.desc())
        .limit(1)
    )
    description = (await db.execute(desc_stmt)).scalar_one_or_none()

    repo_full_name_str = str(row.repo_full_name)
    return PackDetail(
        id=_pack_id_from_repo_full_name(repo_full_name_str),
        repo_full_name=repo_full_name_str,
        repo_url=str(row.repo_url),
        skill_count=int(row.skill_count or 0),
        updated_at=row.updated_at,
        dotclaude_skill_count=int(row.dotclaude_skill_count or 0),
        skills_dir_skill_count=int(row.skills_dir_skill_count or 0),
        description=description,
    )


@router.get("/{id}/skills", response_model=Page[SkillListItem])
async def list_pack_skills(
    id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    repo_full_name_value = _repo_full_name_from_pack_id(id)
    repo_full_name = _repo_full_name_expr()

    stmt = (
        select(Skill)
        .where(*public_skill_conditions())
        .where(repo_full_name == repo_full_name_value)
        .order_by(Skill.updated_at.desc())
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    # Avoid async lazy-load during Pydantic serialization (MissingGreenlet).
    # SkillListItem reads `views/stars/score` via Skill.popularity.
    stmt = stmt.options(selectinload(Skill.category), selectinload(Skill.popularity))
    rows = (await db.execute(stmt)).scalars().all()

    pages = (int(total or 0) + size - 1) // size
    return Page(items=rows, total=int(total or 0), page=page, size=size, pages=pages)
