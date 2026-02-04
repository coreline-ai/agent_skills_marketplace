from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.schemas.admin_skill import AdminSkillCreate, AdminSkillUpdate

class AdminSkillRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_skill(self, payload: AdminSkillCreate) -> Skill:
        """Create a new skill."""
        skill = Skill(
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            author=payload.author,
            content=payload.content,
            inputs=payload.inputs,
            outputs=payload.outputs,
            is_verified=payload.is_verified,
        )
        self.db.add(skill)
        await self.db.flush()
        
        # Init popularity
        pop = SkillPopularity(skill_id=skill.id)
        self.db.add(pop)
        
        # Reload to populate default relationships and avoid MissingGreenlet
        stmt = (
            select(Skill)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
                selectinload(Skill.tag_associations),
                selectinload(Skill.category)
            )
            .where(Skill.id == skill.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_skill(self, skill: Skill, payload: AdminSkillUpdate) -> Skill:
        """Update skill fields."""
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(skill, key, value)
            
        self.db.add(skill)
        await self.db.flush()
        
        # Reload for response
        stmt = (
            select(Skill)
            .options(
                selectinload(Skill.popularity),
                selectinload(Skill.source_links),
                selectinload(Skill.tag_associations),
                selectinload(Skill.category)
            )
            .where(Skill.id == skill.id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
