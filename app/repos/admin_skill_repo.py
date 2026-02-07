from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.models.skill_tag import SkillTag
from app.models.tag import Tag
from app.schemas.admin_skill import AdminSkillCreate, AdminSkillUpdate


class AdminSkillRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_category_id(self, category_slug: Optional[str], *, strict: bool = False):
        if not category_slug:
            return None

        # Taxonomy policy: deprecated categories are merged into Tools.
        if category_slug in {"chat", "code", "writing"}:
            category_slug = "tools"

        stmt = select(Category).where(Category.slug == category_slug)
        result = await self.db.execute(stmt)
        category = result.scalar_one_or_none()
        if strict and not category:
            raise ValueError(f"Unknown category slug: {category_slug}")
        return category.id if category else None

    async def _set_tags(self, skill_id, tags: Optional[list[str]]) -> None:
        await self.db.execute(delete(SkillTag).where(SkillTag.skill_id == skill_id))

        if not tags:
            return

        normalized_tags = sorted({tag.strip().lower() for tag in tags if tag and tag.strip()})
        for slug in normalized_tags:
            stmt = (
                pg_insert(Tag)
                .values(name=slug, slug=slug)
                .on_conflict_do_nothing(index_elements=[Tag.slug])
                .returning(Tag.id)
            )
            inserted = await self.db.execute(stmt)
            tag_id = inserted.scalar_one_or_none()
            if tag_id:
                tag = await self.db.get(Tag, tag_id)
            else:
                existing = await self.db.execute(select(Tag).where(Tag.slug == slug))
                tag = existing.scalar_one_or_none()
                if not tag:
                    # Fallback for legacy rows where name uniqueness may conflict first.
                    existing_by_name = await self.db.execute(select(Tag).where(Tag.name == slug))
                    tag = existing_by_name.scalar_one_or_none()
                if not tag:
                    continue

            self.db.add(SkillTag(skill_id=skill_id, tag_id=tag.id))

    async def create_skill(self, payload: AdminSkillCreate) -> Skill:
        """Create a new skill."""
        category_id = await self._resolve_category_id(
            payload.category_slug,
            strict=bool(payload.category_slug),
        )

        skill = Skill(
            slug=payload.slug,
            name=payload.name,
            description=payload.description or payload.summary,
            author=payload.author,
            content=payload.content,
            url=payload.source_url,
            category_id=category_id,
            inputs=payload.inputs,
            outputs=payload.outputs,
            constraints=payload.constraints,
            triggers=payload.triggers,
            is_official=payload.is_official,
            is_verified=payload.is_verified,
        )
        self.db.add(skill)
        await self.db.flush()

        await self._set_tags(skill.id, payload.tags)

        pop = SkillPopularity(skill_id=skill.id)
        self.db.add(pop)
        await self.db.flush()

        stmt = (
            select(Skill)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
                selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
                selectinload(Skill.category),
            )
            .where(Skill.id == skill.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_skill(self, skill: Skill, payload: AdminSkillUpdate) -> Skill:
        """Update skill fields."""
        update_data = payload.model_dump(exclude_unset=True)
        has_category_slug = "category_slug" in update_data
        category_slug = update_data.pop("category_slug", None)
        has_tags = "tags" in update_data
        tags = update_data.pop("tags", None)

        for key, value in update_data.items():
            if hasattr(Skill, key):
                setattr(skill, key, value)

        if has_category_slug:
            skill.category_id = await self._resolve_category_id(
                category_slug,
                strict=bool(category_slug),
            )

        if has_tags:
            await self._set_tags(skill.id, tags)

        self.db.add(skill)
        await self.db.flush()

        stmt = (
            select(Skill)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
                selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
                selectinload(Skill.category),
            )
            .where(Skill.id == skill.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
