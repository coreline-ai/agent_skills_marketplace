"""Admin Auth & Raw Skills API."""

from datetime import timedelta
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

settings = get_settings()
router = APIRouter()


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Admin login."""
    if (
        form_data.username != settings.admin_username
        or not verify_password(form_data.password, settings.admin_password_hash)
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
    page: int = 1,
    size: int = 20,
):
    """List raw skills in queue."""
    stmt = select(RawSkill)
    if status:
        stmt = stmt.where(RawSkill.parse_status == status)
    
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Mocking total count for now or separate query
    total = 100 # Placeholder
    
    return Page(
        items=[{"id": i.id, "source_url": i.source_url, "status": i.parse_status} for i in items],
        total=total,
        page=page,
        size=size,
        pages=5
    )
