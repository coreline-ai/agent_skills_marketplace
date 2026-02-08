"""Admin Quality Control API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_admin
from app.models.raw_skill import RawSkill
from app.schemas.admin_skill import AdminSkillCreate
from app.schemas.skill_validation_report import SkillValidationReport
from app.repos.admin_skill_repo import AdminSkillRepo
from app.parsers.skillmd_parser import parse_skill_md
from app.quality.claude_skill_spec import validate_claude_skill_frontmatter
from app.workers.ingest_and_parse import normalize_skill_source_url, is_skill_md_source_url, is_canonical_skill_doc_url

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


@router.get("/skill-validation-report", response_model=SkillValidationReport)
async def skill_validation_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
    profile: str = "strict",
    limit: int = 200,
):
    """Dry-run report: how many recent RawSkills would fail Claude spec validation."""
    profile_norm = (profile or "strict").strip().lower()
    if profile_norm not in {"lax", "strict"}:
        profile_norm = "strict"
    limit_norm = max(1, min(int(limit), 5000))

    stmt = (
        select(RawSkill)
        .where(RawSkill.content.is_not(None))
        .order_by(RawSkill.created_at.desc())
        .limit(limit_norm)
    )
    raws = (await db.execute(stmt)).scalars().all()

    examined = 0
    ok = 0
    error = 0
    error_counts: dict[str, int] = {}

    for raw in raws:
        source_url = (raw.source_url or "").strip()
        if not is_skill_md_source_url(source_url):
            continue
        canonical_url = normalize_skill_source_url(source_url) or source_url
        if not is_canonical_skill_doc_url(canonical_url):
            continue

        examined += 1
        parsed = parse_skill_md(raw.content or "")
        metadata = parsed.get("metadata") if isinstance(parsed, dict) else {}
        body = parsed.get("content") if isinstance(parsed, dict) else ""
        frontmatter_raw = parsed.get("frontmatter_raw") if isinstance(parsed, dict) else None
        frontmatter_error = parsed.get("frontmatter_error") if isinstance(parsed, dict) else None

        res = validate_claude_skill_frontmatter(
            metadata=metadata if isinstance(metadata, dict) else {},
            body=body or "",
            canonical_url=canonical_url,
            frontmatter_raw=frontmatter_raw,
            frontmatter_error=frontmatter_error,
            profile=profile_norm,
        )
        if res.ok:
            ok += 1
        else:
            error += 1
            for code in res.errors:
                error_counts[code] = error_counts.get(code, 0) + 1

    top_errors = sorted(error_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    return SkillValidationReport(
        profile=profile_norm, limit=limit_norm, examined=examined, ok=ok, error=error, top_errors=top_errors
    )
