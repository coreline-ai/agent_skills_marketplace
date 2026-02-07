"""Ranking Repository."""

from typing import Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.repos.public_filters import public_skill_conditions

class RankingRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top10_global(self) -> Sequence[Skill]:
        """Get global top 10 skills by popularity score."""
        stmt = (
            select(Skill)
            .outerjoin(Skill.popularity)
            .where(*public_skill_conditions())
            .order_by(desc(SkillPopularity.score).nulls_last(), desc(Skill.created_at))
            .limit(10)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.category)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
