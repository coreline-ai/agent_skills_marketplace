"""Admin Skills CRUD API."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.skill_trust_audit import SkillTrustAudit
from app.schemas.api_key import TrustAuditItem, TrustOverrideRequest
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
    try:
        skill = await repo.create_skill(payload)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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

    try:
        updated_skill = await admin_repo.update_skill(skill, payload)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@router.post("/{id}/trust-override", response_model=SkillDetail)
async def override_skill_trust(
    id: uuid.UUID,
    payload: TrustOverrideRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Admin override for trust score/level/flags."""
    skill_repo = SkillRepo(db)
    skill = await skill_repo.get_skill(id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    before = {
        "trust_score": skill.trust_score,
        "trust_level": skill.trust_level,
        "trust_flags": skill.trust_flags,
        "trust_override": skill.trust_override,
    }
    if payload.trust_score is not None:
        skill.trust_score = float(payload.trust_score)
    if payload.trust_level is not None:
        normalized = payload.trust_level.strip().lower()
        if normalized not in {"ok", "warning", "limited"}:
            raise HTTPException(status_code=400, detail="trust_level must be ok|warning|limited")
        skill.trust_level = normalized
    if payload.trust_flags is not None:
        skill.trust_flags = sorted(
            {str(flag).strip() for flag in payload.trust_flags if str(flag).strip()}
        )
    skill.trust_last_verified_at = datetime.now(timezone.utc)
    skill.trust_override = {
        "actor": str(current_user.get("sub") or "admin"),
        "reason": payload.reason,
        "at": skill.trust_last_verified_at.isoformat(),
    }

    after = {
        "trust_score": skill.trust_score,
        "trust_level": skill.trust_level,
        "trust_flags": skill.trust_flags,
        "trust_override": skill.trust_override,
    }
    db.add(
        SkillTrustAudit(
            skill_id=skill.id,
            actor=str(current_user.get("sub") or "admin"),
            action="override",
            reason=payload.reason,
            before=before,
            after=after,
        )
    )
    await db.commit()
    await db.refresh(skill)
    return skill


@router.get("/{id}/trust-audit", response_model=list[TrustAuditItem])
async def list_skill_trust_audit(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Show trust change history for a skill."""
    _ = current_user
    rows = (
        await db.execute(
            select(SkillTrustAudit)
            .where(SkillTrustAudit.skill_id == id)
            .order_by(desc(SkillTrustAudit.created_at))
            .limit(100)
        )
    ).scalars().all()
    return rows
