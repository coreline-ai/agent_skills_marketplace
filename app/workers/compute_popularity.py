"""Compute Popularity Worker."""

import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.models.skill_event import SkillEvent

async def compute_score(db: AsyncSession):
    """Compute popularity score for all skills."""
    print("Computing popularity scores...")
    
    # 1. Reset/Init
    # In real app: aggregation query from SkillEvent
    # For MVP: just random/mock or simple count
    
    # Example: update score = views * 1 + uses * 10 + favorites * 50
    pass

async def run():
    async with AsyncSessionLocal() as db:
        await compute_score(db)

if __name__ == "__main__":
    asyncio.run(run())
