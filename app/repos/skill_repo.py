"""Skill Repository."""

import uuid
from typing import Sequence, Optional

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import Skill
from app.models.tag import Tag
from app.models.skill_tag import SkillTag
from app.models.category import Category
from app.models.skill_popularity import SkillPopularity
from app.schemas.skill import SkillQuery


class SkillRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_skill(self, skill_id: uuid.UUID) -> Optional[Skill]:
        """Get skill by ID with relations."""
        stmt = (
            select(Skill)
            .where(Skill.id == skill_id)
            .options(
                selectinload(Skill.category),
                selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_skill_by_slug(self, slug: str) -> Optional[Skill]:
        """Get skill by slug."""
        stmt = (
            select(Skill)
            .where(Skill.slug == slug)
            .options(
                selectinload(Skill.category),
                selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_skills(self, query: SkillQuery) -> tuple[Sequence[Skill], int]:
        """List skills with filtering/pagination."""
        stmt = select(Skill).where(Skill.is_official.is_(True)) # Only showing confirmed skills by default? Or all?
        # Maybe show all visible ones. Assuming verified/official is filterable.
        
        # Filter by Query
        if query.q:
            stmt = stmt.where(Skill.name.ilike(f"%{query.q}%"))
        
        if query.category_slug:
            stmt = stmt.join(Skill.category).where(Category.slug == query.category_slug)
            
        if query.tag_slugs:
            # Simple intersection check logic via exists or join
            # For now simplified: has ANY of the tags
            stmt = stmt.join(Skill.tag_associations).join(SkillTag.tag).where(Tag.slug.in_(query.tag_slugs))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Sorting
        if query.sort == "newest":
            stmt = stmt.order_by(desc(Skill.created_at))
        elif query.sort == "oldest":
            stmt = stmt.order_by(Skill.created_at)
        else: # popularity
            # Join popularity if needed
             stmt = stmt.outerjoin(Skill.popularity).order_by(desc(SkillPopularity.score))

        # Pagination
        stmt = stmt.offset((query.page - 1) * query.size).limit(query.size)
        
        # Eager load
        stmt = stmt.options(
            selectinload(Skill.category),
            selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
            selectinload(Skill.popularity),
            selectinload(Skill.source_links),
        )

        result = await self.db.execute(stmt)
        return result.scalars().all(), total
