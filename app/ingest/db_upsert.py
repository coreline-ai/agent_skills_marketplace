"""DB Upsert for Ingestion."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_skill import RawSkill
from app.models.skill_source import SkillSource

async def _ensure_source(db: AsyncSession, name: str, url: str) -> SkillSource:
    """Ensure source exists."""
    stmt = select(SkillSource).where(
        (SkillSource.name == name) | (SkillSource.url == url)
    )
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        source = SkillSource(name=name, url=url, type="github", is_active=True)
        db.add(source)
        await db.flush()
        
    return source

async def upsert_raw_skill(
    db: AsyncSession, 
    source_name: str, 
    external_id: str, 
    content: str,
    url: Optional[str] = None,
    metadata: Optional[dict] = None
) -> RawSkill:
    """Upsert a RawSkill record."""
    source = await _ensure_source(db, source_name, url or "")
    
    stmt = select(RawSkill).where(
        RawSkill.source_id == source.id,
        RawSkill.external_id == external_id
    )
    result = await db.execute(stmt)
    raw = result.scalar_one_or_none()
    
    if raw:
        # Update if content changed
        if raw.content != content:
            raw.content = content
            raw.parse_status = "pending" # Reset status to re-parse
            if metadata:
                raw.parsed_data = metadata # Or merge?
    else:
        # Create
        raw = RawSkill(
            source_id=source.id,
            external_id=external_id,
            source_url=url,
            content=content,
            parsed_data=metadata,
            parse_status="pending"
        )
        db.add(raw)
        
    await db.commit()
    await db.refresh(raw)
    return raw
