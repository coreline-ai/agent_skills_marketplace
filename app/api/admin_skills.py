"""Admin Skills CRUD API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.skill import SkillDetail
from app.schemas.admin_skill import AdminSkillCreate, AdminSkillUpdate
from app.repos.admin_skill_repo import AdminSkillRepo
from app.repos.skill_repo import SkillRepo

router = APIRouter()


@router.post("", response_model=SkillDetail)
async def create_skill(
    payload: AdminSkillCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Create a new skill manually."""
    repo = AdminSkillRepo(db)
    skill = await repo.create_skill(payload)
    await db.commit()
    return skill


@router.patch("/{id}", response_model=SkillDetail)
async def update_skill(
    id: uuid.UUID,
    payload: AdminSkillUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Update an existing skill."""
    skill_repo = SkillRepo(db)
    admin_repo = AdminSkillRepo(db)
    
    skill = await skill_repo.get_skill(id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    updated_skill = await admin_repo.update_skill(skill, payload)
    await db.commit()
    return updated_skill


@router.delete("/{id}")
async def delete_skill(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Delete a skill (Soft delete?)."""
    # Implement soft delete or hard delete
    # For MVP maybe hard delete
    skill_repo = SkillRepo(db)
    skill = await skill_repo.get_skill(id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    await db.delete(skill)
    await db.commit()
    return {"status": "deleted"}
