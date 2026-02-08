"""Admin Auth & Raw Skills API."""

from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.settings import get_settings
from app.security.auth import verify_password, create_access_token
from app.models.raw_skill import RawSkill
from app.models.skill import Skill
from app.schemas.common import Page
from app.ingest.sources import SOURCES
from app.schemas.worker_settings import WorkerSettings, WorkerSettingsPatch
from app.schemas.skill_validation_settings import (
    SkillValidationSettings,
    SkillValidationSettingsPatch,
)
from app.repos.system_setting_repo import (
    get_worker_settings,
    patch_worker_settings,
    get_skill_validation_settings,
    patch_skill_validation_settings,
    get_worker_status_value,
)
from app.schemas.worker_status import WorkerStatus

settings = get_settings()
router = APIRouter()


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Admin login."""
    is_valid = verify_password(form_data.password, settings.admin_password_hash)

    if (
        form_data.username != settings.admin_username
        or not is_valid
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: Annotated[dict, Depends(require_admin)]):
    """Get current admin info."""
    return {"username": current_user["sub"]}


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Aggregated counters for the admin dashboard (avoid guessing from public APIs)."""
    # Skills
    skills_total = (await db.execute(select(func.count()).select_from(Skill))).scalar_one()
    skills_url_null_total = (
        await db.execute(select(func.count()).select_from(Skill).where(Skill.url.is_(None)))
    ).scalar_one()
    skills_public_total = (
        await db.execute(
            select(func.count())
            .select_from(Skill)
            .where(
                Skill.is_official.is_(True),
                Skill.is_verified.is_(True),
                Skill.url.is_not(None),
                or_(
                    Skill.url.op("~*")(
                        r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/skills/[^/]+/SKILL\.md$"
                    ),
                    Skill.url.op("~*")(
                        r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/\.claude/skills/[^/]+/SKILL\.md$"
                    ),
                ),
            )
        )
    ).scalar_one()
    # Public-adjacent URL patterns for debugging "why not public".
    skills_blob_any_depth_total = (
        await db.execute(
            select(func.count())
            .select_from(Skill)
            .where(
                Skill.is_official.is_(True),
                Skill.is_verified.is_(True),
                Skill.url.is_not(None),
                or_(
                    Skill.url.op("~*")(
                        r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/skills/.+/SKILL\.md$"
                    ),
                    Skill.url.op("~*")(
                        r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/\.claude/skills/.+/SKILL\.md$"
                    ),
                ),
            )
        )
    ).scalar_one()
    skills_repo_root_total = (
        await db.execute(
            select(func.count())
            .select_from(Skill)
            .where(
                Skill.is_official.is_(True),
                Skill.is_verified.is_(True),
                Skill.url.is_not(None),
                Skill.url.op("~*")(r"^https://github\.com/[^/]+/[^/]+/?$"),
            )
        )
    ).scalar_one()
    skills_other_total = (
        await db.execute(
            select(func.count())
            .select_from(Skill)
            .where(
                Skill.is_official.is_(True),
                Skill.is_verified.is_(True),
                Skill.url.is_not(None),
                ~Skill.url.op("~*")(r"^https://github\.com/[^/]+/[^/]+/?$"),
                ~Skill.url.op("~*")(r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/(skills|\.claude/skills)/.+/SKILL\.md$"),
            )
        )
    ).scalar_one()
    skills_nested_noncanonical_total = max(
        int(skills_blob_any_depth_total or 0) - int(skills_public_total or 0),
        0,
    )

    # Raw skills
    raw_total = (await db.execute(select(func.count()).select_from(RawSkill))).scalar_one()
    raw_pending = (
        await db.execute(
            select(func.count()).select_from(RawSkill).where(RawSkill.parse_status == "pending")
        )
    ).scalar_one()
    raw_processed = (
        await db.execute(
            select(func.count()).select_from(RawSkill).where(RawSkill.parse_status == "processed")
        )
    ).scalar_one()
    raw_error = (
        await db.execute(
            select(func.count()).select_from(RawSkill).where(RawSkill.parse_status == "error")
        )
    ).scalar_one()

    raw_error_claude_spec = (
        await db.execute(
            select(func.count())
            .select_from(RawSkill)
            .where(RawSkill.parse_status == "error", RawSkill.parse_error["type"].astext == "claude_spec")
        )
    ).scalar_one()
    raw_error_quality = (
        await db.execute(
            select(func.count())
            .select_from(RawSkill)
            .where(RawSkill.parse_status == "error", RawSkill.parse_error["type"].astext == "quality")
        )
    ).scalar_one()

    # Spec coverage: older processed rows may not have claude_spec in parsed_data.
    raw_processed_skill_md = (
        await db.execute(
            select(func.count())
            .select_from(RawSkill)
            .where(
                RawSkill.parse_status == "processed",
                RawSkill.source_url.ilike("%/SKILL.md"),
            )
        )
    ).scalar_one()
    raw_processed_skill_md_missing_spec = (
        await db.execute(
            select(func.count())
            .select_from(RawSkill)
            .where(
                RawSkill.parse_status == "processed",
                RawSkill.source_url.ilike("%/SKILL.md"),
                or_(
                    RawSkill.parsed_data.is_(None),
                    ~RawSkill.parsed_data.has_key("claude_spec"),  # type: ignore[attr-defined]
                ),
            )
        )
    ).scalar_one()

    return {
        "skills_total": int(skills_total or 0),
        "skills_public_total": int(skills_public_total or 0),
        "skills_non_public_total": max(int(skills_total or 0) - int(skills_public_total or 0), 0),
        "skills_url_null_total": int(skills_url_null_total or 0),
        "skills_blob_any_depth_total": int(skills_blob_any_depth_total or 0),
        "skills_nested_noncanonical_total": int(skills_nested_noncanonical_total or 0),
        "skills_repo_root_total": int(skills_repo_root_total or 0),
        "skills_other_total": int(skills_other_total or 0),
        "raw_total": int(raw_total or 0),
        "raw_pending": int(raw_pending or 0),
        "raw_processed": int(raw_processed or 0),
        "raw_error": int(raw_error or 0),
        "raw_error_claude_spec": int(raw_error_claude_spec or 0),
        "raw_error_quality": int(raw_error_quality or 0),
        "raw_processed_skill_md": int(raw_processed_skill_md or 0),
        "raw_processed_skill_md_missing_spec": int(raw_processed_skill_md_missing_spec or 0),
    }


@router.get("/worker-status", response_model=WorkerStatus)
async def get_worker_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Return the worker heartbeat (best-effort)."""
    value = await get_worker_status_value(db)
    if not isinstance(value, dict):
        return WorkerStatus()
    try:
        return WorkerStatus.model_validate(value)
    except Exception:
        # Don't fail admin UI due to a malformed row.
        return WorkerStatus()


@router.get("/raw-skills", response_model=Page[dict]) # TODO: Use RawSkill schema
async def list_raw_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
    status: Optional[str] = "pending",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List raw skills in queue."""
    stmt = select(RawSkill)
    if status:
        stmt = stmt.where(RawSkill.parse_status == status)
    
    # Count total
    count_stmt = select(func.count()).select_from(RawSkill)
    if status:
        count_stmt = count_stmt.where(RawSkill.parse_status == status)
    
    total = (await db.execute(count_stmt)).scalar_one()
    
    stmt = stmt.order_by(RawSkill.created_at.desc()) # Newest first
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    total_pages = (total + size - 1) // size
    
    return Page(
        items=[
            {
                "id": i.id,
                "source_url": i.source_url,
                "external_id": i.external_id,
                "status": i.parse_status,
                "parse_error": i.parse_error,
                "created_at": i.created_at,
            }
            for i in items
        ],
        total=total,
        page=page,
        size=size,
        pages=total_pages
    )


@router.post("/raw-skills/reparse")
async def reparse_raw_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
    limit: int = Query(100, ge=1, le=5000),
    only_skill_md: bool = Query(True),
    only_missing_claude_spec: bool = Query(True),
):
    """
    Force re-parse/re-validate existing RawSkills by setting parse_status back to "pending".

    This is useful when you introduce new validation/normalization logic (e.g. Claude SKILL.md spec),
    because the worker only re-parses items whose content changed.
    """
    stmt = select(RawSkill.id).where(RawSkill.parse_status == "processed")
    if only_skill_md:
        stmt = stmt.where(
            or_(
                RawSkill.source_url.ilike("%/SKILL.md"),
                RawSkill.external_id.ilike("%/SKILL.md"),
            )
        )
    if only_missing_claude_spec:
        # Only reparse rows that were processed by older builds (no spec validation output yet).
        stmt = stmt.where(
            or_(
                RawSkill.parsed_data.is_(None),
                ~RawSkill.parsed_data.has_key("claude_spec"),  # type: ignore[attr-defined]
            )
        )
    stmt = stmt.order_by(RawSkill.updated_at.desc()).limit(limit)
    ids = (await db.execute(stmt)).scalars().all()
    if not ids:
        return {"updated": 0}

    await db.execute(
        update(RawSkill)
        .where(RawSkill.id.in_(ids))
        .values(parse_status="pending", parse_error=None)
    )
    await db.commit()
    return {"updated": len(ids)}


from fastapi import BackgroundTasks
from app.workers import ingest_and_parse

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingest(
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Trigger background ingestion."""
    background_tasks.add_task(ingest_and_parse.run)
    return {"status": "ingestion started"}


@router.get("/crawl-sources", response_model=list[dict])
async def list_crawl_sources(
    current_user: Annotated[dict, Depends(require_admin)],
):
    """List configured crawl sources with repository intent policy."""
    items = []
    seen_repos: set[str] = set()
    seen_directories: set[str] = set()

    for source in SOURCES:
        source_type = str(source.get("type", "")).strip()
        if source_type == "github_repo":
            repo_full_name = str(source.get("repo_full_name", "")).strip()
            if not repo_full_name or repo_full_name in seen_repos:
                continue
            seen_repos.add(repo_full_name)
            items.append(
                {
                    "id": source.get("id"),
                    "source_type": "github_repo",
                    "repo_full_name": repo_full_name,
                    "url": f"https://github.com/{repo_full_name}",
                    "policy": {
                        "min_repo_type": source.get("min_repo_type", "skills_focused"),
                        "allowed_path_globs": source.get("allowed_path_globs") or [],
                    },
                }
            )
            continue

        if source_type == "web_directory":
            directory_url = str(source.get("url", "")).strip()
            if not directory_url or directory_url in seen_directories:
                continue
            seen_directories.add(directory_url)
            items.append(
                {
                    "id": source.get("id"),
                    "source_type": "web_directory",
                    "repo_full_name": None,
                    "url": directory_url,
                    "policy": {
                        "min_repo_type": source.get("min_repo_type", "skills_only"),
                        "max_repos": source.get("max_repos"),
                        "max_sitemap_pages": source.get("max_sitemap_pages"),
                        "allowed_path_globs": source.get("allowed_path_globs") or [],
                    },
                }
            )
            continue

        if source_type == "github_search":
            source_id = str(source.get("id", "")).strip()
            if not source_id:
                continue
            queries = [str(q).strip() for q in source.get("queries", []) if str(q).strip()]
            preview_query = queries[0] if queries else ""
            search_url = "https://github.com/search"
            if preview_query:
                from urllib.parse import quote_plus
                search_url = f"https://github.com/search?q={quote_plus(preview_query)}&type=code"
            items.append(
                {
                    "id": source_id,
                    "source_type": "github_search",
                    "repo_full_name": None,
                    "url": search_url,
                    "policy": {
                        "search_mode": source.get("search_mode", "code"),
                        "require_token": source.get("require_token", True),
                        "query_count": len(queries),
                        "min_repo_type": source.get("min_repo_type", "skills_only"),
                        "max_repos": source.get("max_repos"),
                        "max_pages": source.get("max_pages"),
                        "allowed_path_globs": source.get("allowed_path_globs") or [],
                    },
                }
            )

    def _sort_key(item: dict) -> tuple[str, str]:
        return (
            str(item.get("source_type", "")),
            str(item.get("repo_full_name") or item.get("url") or "").lower(),
        )

    items.sort(key=_sort_key)
    return items


@router.get("/worker-settings", response_model=WorkerSettings)
async def read_worker_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Read runtime settings used by the worker loop."""
    return await get_worker_settings(db)


@router.patch("/worker-settings", response_model=WorkerSettings)
async def update_worker_settings(
    payload: WorkerSettingsPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Update runtime settings used by the worker loop."""
    try:
        updated = await patch_worker_settings(db, payload)
        await db.commit()
        return updated
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/skill-validation-settings", response_model=SkillValidationSettings)
async def read_skill_validation_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Read skill validation/enforcement settings used by ingestion."""
    return await get_skill_validation_settings(db)


@router.patch("/skill-validation-settings", response_model=SkillValidationSettings)
async def update_skill_validation_settings(
    payload: SkillValidationSettingsPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Update skill validation/enforcement settings used by ingestion."""
    try:
        updated = await patch_skill_validation_settings(db, payload)
        await db.commit()
        return updated
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
