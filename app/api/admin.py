"""Admin Auth & Raw Skills API."""

from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.settings import get_settings
from app.security.auth import verify_password, create_access_token
from app.models.raw_skill import RawSkill
from app.schemas.common import Page
from app.ingest.sources import SOURCES
from app.schemas.worker_settings import WorkerSettings, WorkerSettingsPatch
from app.repos.system_setting_repo import get_worker_settings, patch_worker_settings

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
    from sqlalchemy import func
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
