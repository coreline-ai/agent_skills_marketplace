"""Ranking Repository."""

from typing import Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity

class RankingRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top10_global(self) -> Sequence[Skill]:
        """Get global top 10 skills by popularity score."""
        stmt = (
            select(Skill)
            .join(Skill.popularity)
            .order_by(desc(SkillPopularity.score))
            .limit(10)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.category)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
