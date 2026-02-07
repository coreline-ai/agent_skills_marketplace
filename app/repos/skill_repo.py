"""Skill Repository."""

import uuid
from typing import Sequence, Optional

from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import Skill
from app.models.tag import Tag
from app.models.skill_tag import SkillTag
from app.models.category import Category
from app.models.skill_popularity import SkillPopularity
from app.schemas.skill import SkillQuery
from app.repos.public_filters import public_skill_conditions


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
        stmt = select(Skill).where(*public_skill_conditions())
        
        # Filter by Query
        if query.q:
            keyword = query.q.strip()
            if keyword:
                like = f"%{keyword}%"
                tag_search_exists = (
                    select(SkillTag.skill_id)
                    .join(Tag, SkillTag.tag_id == Tag.id)
                    .where(
                        SkillTag.skill_id == Skill.id,
                        or_(Tag.name.ilike(like), Tag.slug.ilike(like)),
                    )
                    .exists()
                )
                stmt = stmt.where(
                    or_(
                        Skill.name.ilike(like),
                        Skill.slug.ilike(like),
                        Skill.description.ilike(like),
                        Skill.content.ilike(like),
                        tag_search_exists,
                    )
                )
        
        if query.category_slug:
            stmt = stmt.join(Skill.category).where(Category.slug == query.category_slug)
            
        if query.tag_slugs:
            # ANY semantics: include skills that have at least one selected tag.
            tag_filter_exists = (
                select(SkillTag.skill_id)
                .join(Tag, SkillTag.tag_id == Tag.id)
                .where(
                    SkillTag.skill_id == Skill.id,
                    Tag.slug.in_(query.tag_slugs),
                )
                .exists()
            )
            stmt = stmt.where(tag_filter_exists)

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
