"""Admin Quality Control API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_admin
from app.models.raw_skill import RawSkill
from app.schemas.admin_skill import AdminSkillCreate
from app.repos.admin_skill_repo import AdminSkillRepo

router = APIRouter()


@router.get("/raw-skills/{id}/preview")
async def preview_raw_skill(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Preview parsed content of a raw skill before approval."""
    stmt = select(RawSkill).where(RawSkill.id == id)
    result = await db.execute(stmt)
    raw = result.scalar_one_or_none()
    
    if not raw:
        raise HTTPException(status_code=404, detail="Raw skill not found")
        
    # In real app: Parse raw.content (SKILL.md) dynamically here
    return {"content_preview": raw.content, "parsed_metadata": raw.parsed_data}


@router.post("/raw-skills/approve")
async def approve_skill(
    payload: AdminSkillCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Approve a raw skill (turns it into a real Skill)."""
    repo = AdminSkillRepo(db)
    try:
        skill = await repo.create_skill(payload)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    # Mark RawSkill as processed if linked
    if payload.source_link and "external_id" in payload.source_link:
        # Complex logic to find raw skill by external_id and update status
        pass
    
    await db.commit()
    return skill
