"""Seed data script."""

import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.category import Category
from app.models.skill_source import SkillSource

INITIAL_CATEGORIES = [
    {"name": "Chat", "slug": "chat", "description": "Chat and conversation skills"},
    {"name": "Code", "slug": "code", "description": "Programming and development"},
    {"name": "Writing", "slug": "writing", "description": "Text generation and editing"},
    {"name": "Productivity", "slug": "productivity", "description": "Workflow automation"},
    {"name": "Data", "slug": "data", "description": "Data analysis and processing"},
]

INITIAL_SOURCES = [
    {
        "name": "Awesome Agents",
        "url": "https://raw.githubusercontent.com/kyrolabs/awesome-agents/main/README.md",
        "type": "markdown_list"
    },
    {
        "name": "Model Context Protocol Skills",
        "url": "https://github.com/modelcontextprotocol/servers", # Example
        "type": "github_repo"
    }
]

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("Seeding Categories...")
        for cat_data in INITIAL_CATEGORIES:
            stmt = select(Category).where(Category.slug == cat_data["slug"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                cat = Category(**cat_data, display_order=0)
                db.add(cat)
                
        print("Seeding Sources...")
        for src_data in INITIAL_SOURCES:
            stmt = select(SkillSource).where(SkillSource.name == src_data["name"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                src = SkillSource(**src_data)
                db.add(src)
                
        await db.commit()
        print("Seed Complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
