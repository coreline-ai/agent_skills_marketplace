"""Build Ranking Snapshots Worker."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
# from app.models.skill_rank_snapshot import SkillRankSnapshot

async def run():
    async with AsyncSessionLocal() as db:
        print("Building rank snapshots...")
        pass

if __name__ == "__main__":
    asyncio.run(run())
