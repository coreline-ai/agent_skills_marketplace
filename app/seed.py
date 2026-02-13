import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.category import Category
from app.models.skill_source import SkillSource
from app.models.skill import Skill
from app.models.tag import Tag
from app.models.skill_tag import SkillTag
from app.models.skill_popularity import SkillPopularity

INITIAL_CATEGORIES = [
    # Taxonomy policy: "chat", "code", "writing" are deprecated and merged into Tools.
    {"name": "Tools", "slug": "tools", "description": "Plugins, utilities, and general-purpose skills"},
    {"name": "Frameworks", "slug": "frameworks", "description": "Agent runtimes and orchestration frameworks"},
    {"name": "Coding", "slug": "coding", "description": "Programming and development"},
    {"name": "Research", "slug": "research", "description": "Research and analysis"},
    {"name": "Memory", "slug": "memory", "description": "Memory and context management"},
    {"name": "Robotics", "slug": "robotics", "description": "Robotics and embodied agents"},
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

INITIAL_SKILLS = [
    {
        "slug": "google/stitch-mcp",
        "name": "Stitch MCP",
        "description": "Stitch generates UIs for mobile and web applications, making design ideation fast and easy.",
        "author": "Google",
        "url": "https://stitch.withgoogle.com/docs/mcp/setup",
        "category_slug": "tools",
        "tags": ["design", "ui", "frontend", "mcp"],
        "content": """# Stitch MCP Setup

## Installation

### Claude Code
```bash
claude mcp add stitch --transport http https://stitch.googleapis.com/mcp --header X-Goog-Api-Key:YOUR-API-KEY
```

### Cursor
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "stitch": {
      "url": "https://stitch.googleapis.com/mcp",
      "headers": {
        "X-Goog-Api-Key": "YOUR-API-KEY"
      }
    }
  }
}
```

### VSCode (with MCP extension)
1. Open Command Palette (`Cmd/Ctrl + Shift + P`) -> **MCP: Add Server**
2. Transport: **HTTP**
3. URL: `https://stitch.googleapis.com/mcp`
4. Name: `stitch`
5. Headers:
```json
{
  "headers": {
    "Accept": "application/json",
    "X-Goog-Api-Key": "YOUR-API-KEY"
  }
}
```

### Gemini CLI
```bash
gemini extensions install https://github.com/gemini-cli-extensions/stitch
```

## Configuration
1.  Get API Key from [Stitch Settings](https://stitch.withgoogle.com/settings).
2.  MCP Server URL: `https://stitch.googleapis.com/mcp`
3.  Header: `X-Goog-Api-Key: YOUR-API-KEY`
""",
        "is_verified": True,
        "is_official": True,
        "inputs": {},
        "outputs": {},
        "github_stars": 1250,
        "use_cases": [
            "Quickly prototype mobile app UIs",
            "Generate React components from text descriptions",
            "Speed up design-to-code workflow"
        ]
    }
]

async def backfill_uncategorized_skills(db):
    """Assign categories to existing skills that have category_id = NULL.

    Uses the same keyword-based classification from ingest_and_parse.py.
    This covers the scenario where skills were created in production
    before the categories table was seeded.
    """
    from app.workers.ingest_and_parse import classify_category_slug

    # Build category lookup
    cat_result = await db.execute(select(Category))
    categories = cat_result.scalars().all()
    category_id_by_slug = {c.slug: c.id for c in categories}
    fallback_category_id = (
        category_id_by_slug.get("tools")
        or next(iter(category_id_by_slug.values()), None)
    )

    if not category_id_by_slug:
        print("  No categories found, skipping backfill.")
        return

    # Find skills without a category
    stmt = select(Skill).where(Skill.category_id.is_(None))
    result = await db.execute(stmt)
    uncategorized = result.scalars().all()

    if not uncategorized:
        print("  All skills already have categories assigned.")
        return

    print(f"  Backfilling {len(uncategorized)} uncategorized skill(s)...")
    for skill in uncategorized:
        slug = classify_category_slug(skill.name or "", skill.description or "")
        skill.category_id = category_id_by_slug.get(slug, fallback_category_id)

    await db.flush()
    print(f"  Backfill complete.")


async def seed_data():
    async with AsyncSessionLocal() as db:
        print("Seeding Categories...")
        for cat_data in INITIAL_CATEGORIES:
            stmt = select(Category).where(Category.slug == cat_data["slug"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                cat = Category(**cat_data, display_order=0)
                db.add(cat)
        
        await db.flush() # Ensure categories have IDs and are queryable
                
        print("Seeding Sources...")
        for src_data in INITIAL_SOURCES:
            stmt = select(SkillSource).where(SkillSource.name == src_data["name"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                src = SkillSource(**src_data)
                db.add(src)

        print("Seeding Skills...")
        for skill_data in INITIAL_SKILLS:
            stmt = select(Skill).where(Skill.slug == skill_data["slug"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                # Get category
                cat_stmt = select(Category).where(Category.slug == skill_data["category_slug"])
                cat_result = await db.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                
                if category:
                    # Create Skill
                    new_skill = Skill(
                        slug=skill_data["slug"],
                        name=skill_data["name"],
                        description=skill_data["description"],
                        author=skill_data["author"],
                        url=skill_data["url"],
                        category_id=category.id,
                        content=skill_data["content"],
                        is_verified=skill_data["is_verified"],
                        is_official=skill_data["is_official"],
                        inputs=skill_data.get("inputs"),
                        outputs=skill_data.get("outputs"),
                        github_stars=skill_data.get("github_stars"),
                        use_cases=skill_data.get("use_cases")
                    )
                    db.add(new_skill)
                    await db.flush() # to get ID
                    
                    # Create Popularity
                    popularity = SkillPopularity(skill_id=new_skill.id)
                    db.add(popularity)

                    # Handle Tags
                    for tag_name in skill_data["tags"]:
                        tag_slug = tag_name.lower().replace(" ", "-") # Simple slugify
                        tag_stmt = select(Tag).where(Tag.slug == tag_slug)
                        tag_result = await db.execute(tag_stmt)
                        tag = tag_result.scalar_one_or_none()
                        
                        if not tag:
                            tag = Tag(name=tag_name, slug=tag_slug)
                            db.add(tag)
                            await db.flush()
                        
                        skill_tag = SkillTag(skill_id=new_skill.id, tag_id=tag.id)
                        db.add(skill_tag)

        # Backfill categories for any existing uncategorized skills
        print("Backfilling uncategorized skills...")
        await backfill_uncategorized_skills(db)

        await db.commit()
        print("Seed Complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
