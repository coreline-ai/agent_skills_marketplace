"""Ingest and Parse Worker."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.ingest.sources import run_ingest_sources
from app.ingest.db_upsert import upsert_raw_skill
from app.models.raw_skill import RawSkill
from app.parsers.skillmd_parser import parse_skill_md
from app.repos.admin_skill_repo import AdminSkillRepo
from app.schemas.admin_skill import AdminSkillCreate, AdminSkillUpdate

async def ingest_raw(db: AsyncSession):
    """Fetch from sources and upsert raw skills."""
    print("Fetching sources...")
    results = await run_ingest_sources()
    
    count = 0
    for res in results:
        # For MVP, assume source content is a list or we parse the single File
        # If it's a list (like awesome-agents), we might need to parse links there
        # For now, treating the content as text
        pass
        
    print(f"Ingested {count} raw items.")

async def parse_queued_raw_skills(db: AsyncSession):
    """Process pending raw skills."""
    print("Processing pending raw skills...")
    stmt = select(RawSkill).where(RawSkill.parse_status == "pending").limit(50)
    result = await db.execute(stmt)
    pending_skills = result.scalars().all()
    
    for raw in pending_skills:
        try:
            parsed = parse_skill_md(raw.content)
            raw.parsed_data = parsed
            raw.parse_status = "processed"
            # Auto-create skill if needed? Or just leave for admin review?
            # For MVP, let's leave for admin review or Auto-Approve based on config
        except Exception as e:
            print(f"Error parsing raw skill {raw.id}: {e}")
            raw.parse_status = "error"
            
    await db.commit()

async def run():
    """Run ingest and parse workflow."""
    async with AsyncSessionLocal() as db:
        await ingest_raw(db)
        await parse_queued_raw_skills(db)

if __name__ == "__main__":
    asyncio.run(run())
