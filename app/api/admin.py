"""Admin Auth & Raw Skills API."""

from datetime import timedelta, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.settings import get_settings
from app.security.auth import verify_password, create_access_token
from app.models.raw_skill import RawSkill
from app.schemas.common import Page
from app.ingest.sources import SOURCES

settings = get_settings()
router = APIRouter()


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Admin login."""
    # DEBUGGING: Write to file to persist logs
    with open("auth_debug.log", "a") as f:
        f.write(f"\\n--- Login Attempt ---\\n")
        f.write(f"Timestamp: {datetime.now()}\\n")
        f.write(f"Received Username: '{form_data.username}'\\n")
        f.write(f"Settings Username: '{settings.admin_username}'\\n")
        f.write(f"Password Len: {len(form_data.password)}\\n")
        f.write(f"Password Repr: {repr(form_data.password)}\\n") # REVEAL THE MYSTERY
        
        # Verify
        try:
            is_valid = verify_password(form_data.password, settings.admin_password_hash)
            f.write(f"Hash Verification Result: {is_valid}\\n")
        except Exception as e:
            f.write(f"Hash Verification Error: {e}\\n")
            is_valid = False

    if (
        form_data.username != settings.admin_username
        or not is_valid
    ):
        with open("auth_debug.log", "a") as f:
            f.write("Result: AUTH FAILED\\n")
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    with open("auth_debug.log", "a") as f:
        f.write("Result: AUTH SUCCESS\\n")
    
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
    page: int = 1,
    size: int = 20,
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
    """List configured GitHub crawl sources."""
    items = []
    seen: set[str] = set()

    for source in SOURCES:
        if source.get("type") != "github_repo":
            continue
        repo_full_name = str(source.get("repo_full_name", "")).strip()
        if not repo_full_name or repo_full_name in seen:
            continue
        seen.add(repo_full_name)
        items.append(
            {
                "id": source.get("id"),
                "repo_full_name": repo_full_name,
                "url": f"https://github.com/{repo_full_name}",
            }
        )

    items.sort(key=lambda item: item["repo_full_name"].lower())
    return items
