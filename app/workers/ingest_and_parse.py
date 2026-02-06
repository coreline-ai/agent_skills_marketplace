"""Ingest and Parse Worker."""

import asyncio
import hashlib
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from urllib.parse import urlparse

from app.db.session import AsyncSessionLocal
from app.ingest.sources import run_ingest_sources
from app.ingest.db_upsert import upsert_raw_skill
from app.models.raw_skill import RawSkill
from app.parsers.skillmd_parser import parse_skill_md

CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("robotics", ["robot", "robotic", "ros", "embodied", "drone", "autonomous vehicle"]),
    ("memory", ["memory", "long-term", "vector store", "context window", "recall"]),
    ("research", ["research", "paper", "literature", "analysis", "experiment", "arxiv"]),
    ("coding", ["code", "developer", "programming", "debug", "refactor", "ide", "repo", "pull request"]),
    ("frameworks", ["framework", "sdk", "library", "orchestr", "multi-agent", "agent runtime"]),
    ("tools", ["tool", "plugin", "extension", "cli", "assistant", "automation utility"]),
    ("data", ["data", "etl", "sql", "analytics", "dataset", "pipeline"]),
    ("productivity", ["productivity", "workflow", "task", "calendar", "notes"]),
    ("writing", ["writing", "copywriting", "blog", "content generation", "summarize"]),
    ("chat", ["chat", "conversation", "chatbot", "assistant bot"]),
]

SKILL_INCLUDE_KEYWORDS = [
    "agent",
    "agents",
    "autonomous",
    "assistant",
    "autogen",
    "copilot",
    "workflow",
    "orchestr",
    "multi-agent",
    "llm",
    "gpt",
    "rag",
    "chatbot",
    "prompt",
    "crewai",
    "devin",
    "langchain",
    "llamaindex",
]

SKILL_EXCLUDE_KEYWORDS = [
    "awesome-",
    "papers",
    "paper list",
    "benchmark",
    "dataset",
    "newsletter",
    "course",
    "jobs",
    "interview",
    "roadmap",
]
GENERIC_LINK_NAMES = {"github", "repo", "repository", "source"}

MARKDOWN_BULLET_LINK_PATTERN = re.compile(
    r"^\s*[-*]\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s*(?:[-:–—]\s*(.+))?$"
)
MARKDOWN_HEADER_LINK_PATTERN = re.compile(
    r"^\s*#{2,4}\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s*$"
)
GENERIC_GITHUB_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((https?://github\.com/[^)\s]+)\)"
)


def classify_category_slug(name: str, description: str) -> str:
    """Return a normalized category slug based on keyword heuristics."""
    haystack = f"{name} {description}".lower()
    for slug, keywords in CATEGORY_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return slug
    return "tools"


def normalize_github_repo_url(url: str) -> Optional[str]:
    """Normalize URL to canonical GitHub repo URL (owner/repo)."""
    raw = (url or "").strip()
    if not raw.lower().startswith(("http://", "https://")):
        return None

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]
    if "raw.githubusercontent.com" in host:
        # /{owner}/{repo}/{branch}/{path...}
        if len(parts) < 3:
            return None
        owner, repo = parts[0], parts[1]
    elif "github.com" in host:
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
    else:
        return None

    if owner.lower() in {
        "topics",
        "search",
        "orgs",
        "collections",
        "apps",
        "features",
        "marketplace",
        "login",
        "settings",
        "explore",
        "sponsors",
    }:
        return None
    if repo.endswith(".git"):
        repo = repo[:-4]
    return f"https://github.com/{owner}/{repo}"


def is_skill_md_source_url(url: Optional[str]) -> bool:
    """Check whether the raw source points to a SKILL.md document."""
    if not url:
        return False
    return urlparse(url).path.lower().endswith("/skill.md")


def slugify_text(value: str) -> str:
    """Create a URL-friendly slug fragment."""
    return re.sub(r"[^a-z0-9-]", "", value.lower().replace(" ", "-").replace("/", "-")).strip("-")


def is_skill_candidate(name: str, description: str, canonical_url: str) -> bool:
    """Heuristic quality gate: keep only skill/agent-like repositories."""
    path_parts = [p for p in urlparse(canonical_url).path.split("/") if p]
    repo_name = path_parts[1] if len(path_parts) >= 2 else ""
    text = f"{name} {description} {repo_name}".lower()

    if any(keyword in text for keyword in SKILL_EXCLUDE_KEYWORDS):
        return False
    return any(keyword in text for keyword in SKILL_INCLUDE_KEYWORDS)


def normalize_skill_name(raw_name: str, canonical_url: str) -> str:
    """Replace generic link names with the repository name."""
    name = (raw_name or "").strip()
    lowered = name.lower()
    if lowered in GENERIC_LINK_NAMES or len(name) < 2:
        parts = [p for p in urlparse(canonical_url).path.split("/") if p]
        if len(parts) >= 2:
            repo = parts[1]
            return repo.replace("-", " ").replace("_", " ").strip() or repo
    return name


def derive_skill_name(metadata: dict, source_url: Optional[str], fallback_url: str) -> str:
    """Derive a stable skill name from metadata or SKILL.md path."""
    for key in ("name", "title", "skill_name"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    target_url = source_url or fallback_url
    path_parts = [p for p in urlparse(target_url).path.split("/") if p]
    if len(path_parts) >= 2:
        folder_name = path_parts[-2]
        pretty = folder_name.replace("-", " ").replace("_", " ").strip()
        if pretty:
            return pretty.title()

    canonical = normalize_github_repo_url(target_url)
    if canonical:
        repo_name = canonical.rstrip("/").split("/")[-1]
        return repo_name.replace("-", " ").replace("_", " ").title()
    return "Unknown Skill"


def derive_skill_description(metadata: dict, body: str) -> str:
    """Derive a concise description from frontmatter/body."""
    for key in ("description", "summary"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for line in body.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith(("#", "-", "*", "```", ">")):
            continue
        return text[:220]
    return "No description provided."


def extract_skill_candidates_from_markdown(content: str) -> list[dict[str, str]]:
    """
    Extract skill-like links from markdown list pages.
    Supports bullet links and heading links used by popular awesome lists.
    """
    lines = content.splitlines()
    candidates: list[dict[str, str]] = []

    for idx, line in enumerate(lines):
        bullet_match = MARKDOWN_BULLET_LINK_PATTERN.match(line)
        if bullet_match:
            name = bullet_match.group(1).strip()
            url = bullet_match.group(2).strip()
            description = (bullet_match.group(3) or "").strip()
            candidates.append({"name": name, "url": url, "description": description})
            continue

        header_match = MARKDOWN_HEADER_LINK_PATTERN.match(line)
        if header_match:
            name = header_match.group(1).strip()
            url = header_match.group(2).strip()
            description = ""

            # Capture one nearby plain-text line as a lightweight description.
            for next_line in lines[idx + 1 : idx + 4]:
                text = next_line.strip()
                if not text:
                    continue
                if text.startswith(("#", "-", "*", "|", ">", "```")):
                    break
                description = text
                break

            candidates.append({"name": name, "url": url, "description": description})

    known_urls = {candidate["url"] for candidate in candidates}
    for match in GENERIC_GITHUB_LINK_PATTERN.finditer(content):
        name = match.group(1).strip()
        url = match.group(2).strip()
        if url in known_urls:
            continue
        candidates.append({"name": name, "url": url, "description": ""})
        known_urls.add(url)

    return candidates

async def ingest_raw(db: AsyncSession):
    """Fetch from sources and upsert raw skills."""
    print("Fetching sources...")
    results = await run_ingest_sources()
    
    count = 0
    for res in results:
        # res has keys: source_id, content, url
        source_id = res["source_id"]
        content = res["content"]
        url = res["url"]
        
        external_id = res.get("external_id") or url
        
        await upsert_raw_skill(
            db=db,
            source_name=source_id,
            external_id=external_id,
            content=content,
            url=url,
            metadata={
                "ingested_at": "now",
                "source_type": res.get("source_type", "markdown_list"),
                "repo_full_name": res.get("repo_full_name"),
                "skill_path": res.get("skill_path"),
                "skill_sha": res.get("skill_sha"),
            },
        )
        count += 1
        
    print(f"Ingested {count} raw items.")



async def parse_queued_raw_skills(db: AsyncSession):
    """Process pending raw skills."""
    print("Processing pending raw skills...")
    stmt = select(RawSkill).where(RawSkill.parse_status == "pending").limit(50)
    result = await db.execute(stmt)
    pending_skills = result.scalars().all()

    import uuid
    from app.models.skill import Skill
    
    # Build category lookup map once to avoid single-category assignment bugs.
    from app.models.category import Category
    cat_result = await db.execute(select(Category))
    categories = cat_result.scalars().all()
    category_id_by_slug = {category.slug: category.id for category in categories}
    fallback_category_id = (
        category_id_by_slug.get("tools")
        or category_id_by_slug.get("frameworks")
        or category_id_by_slug.get("coding")
        or category_id_by_slug.get("chat")
        or next(iter(category_id_by_slug.values()), None)
    )
    
    for raw in pending_skills:
        try:
            print(f"DEBUG: Processing RawSkill {raw.id} | URL: '{raw.source_url}'")

            content = raw.content or ""
            if is_skill_md_source_url(raw.source_url):
                parsed = parse_skill_md(content)
                metadata = parsed.get("metadata") or {}
                body = parsed.get("content") or ""
                source_url = raw.source_url or ""
                canonical_url = normalize_github_repo_url(source_url) or source_url

                name = derive_skill_name(metadata, source_url, canonical_url)
                description = derive_skill_description(metadata, body)

                category_slug = None
                raw_category = metadata.get("category")
                if isinstance(raw_category, str) and raw_category.strip():
                    category_slug = slugify_text(raw_category)
                if not category_slug:
                    category_slug = classify_category_slug(name, description)
                category_id = category_id_by_slug.get(category_slug, fallback_category_id)

                existing_skill = (
                    await db.execute(select(Skill).where(Skill.url == canonical_url).limit(1))
                ).scalar_one_or_none()
                if existing_skill:
                    if name:
                        existing_skill.name = name
                    if description:
                        existing_skill.description = description
                    if body:
                        existing_skill.content = body
                    if category_id:
                        existing_skill.category_id = category_id
                    existing_skill.is_official = True
                    existing_skill.is_verified = True
                    created_count = 0
                    updated_count = 1
                else:
                    slug_base = slugify_text(name) or "skill"
                    slug_seed = canonical_url or source_url
                    slug = f"{slug_base}-{hashlib.sha1(slug_seed.encode()).hexdigest()[:10]}"
                    unique_slug = slug
                    suffix = 1
                    while (await db.execute(select(Skill.id).where(Skill.slug == unique_slug))).scalar_one_or_none():
                        unique_slug = f"{slug}-{suffix}"
                        suffix += 1

                    new_skill = Skill(
                        name=name,
                        slug=unique_slug,
                        description=description,
                        content=body,
                        category_id=category_id,
                        url=canonical_url,
                        is_official=True,
                        is_verified=True,
                    )
                    db.add(new_skill)
                    created_count = 1
                    updated_count = 0

                raw.parsed_data = {
                    "source_type": "skill_md",
                    "name": name,
                    "category_slug": category_slug,
                    "extracted_count": created_count,
                    "updated_count": updated_count,
                }
                raw.parse_error = None
                raw.parse_status = "processed"
                await db.flush()
                continue

            candidates = extract_skill_candidates_from_markdown(content)

            if candidates:
                created_count = 0
                updated_count = 0
                skipped_non_skill_count = 0
                category_distribution: dict[str, int] = {}
                seen_urls: set[str] = set()

                for candidate in candidates:
                    name = candidate["name"]
                    desc = candidate["description"]
                    link = candidate["url"]
                    canonical_url = normalize_github_repo_url(link)

                    if not canonical_url or canonical_url in seen_urls:
                        continue
                    seen_urls.add(canonical_url)
                    name = normalize_skill_name(name, canonical_url)

                    if not is_skill_candidate(name, desc, canonical_url):
                        skipped_non_skill_count += 1
                        continue

                    category_slug = classify_category_slug(name, desc)
                    category_id = category_id_by_slug.get(category_slug, fallback_category_id)
                    if not category_id:
                        print("Error: No category found. Skipping.")
                        continue

                    existing_stmt = select(Skill).where(Skill.url == canonical_url).limit(1)
                    existing_skill = (await db.execute(existing_stmt)).scalar_one_or_none()
                    if existing_skill:
                        if not existing_skill.name:
                            existing_skill.name = name
                        if desc and (not existing_skill.description or len(existing_skill.description) < 30):
                            existing_skill.description = desc
                        if not existing_skill.category_id:
                            existing_skill.category_id = category_id
                        existing_skill.is_official = True
                        existing_skill.is_verified = True
                        updated_count += 1
                    else:
                        skill_id = str(uuid.uuid4())
                        slug_base = name.lower().replace(" ", "-").replace("/", "-")
                        slug_base = re.sub(r"[^a-z0-9-]", "", slug_base).strip("-") or "skill"
                        slug = f"{slug_base}-{hashlib.sha1(canonical_url.encode()).hexdigest()[:10]}"

                        # Keep slug unique even when names collide.
                        unique_slug = slug
                        suffix = 1
                        while (await db.execute(select(Skill.id).where(Skill.slug == unique_slug))).scalar_one_or_none():
                            unique_slug = f"{slug}-{suffix}"
                            suffix += 1

                        new_skill = Skill(
                            id=skill_id,
                            name=name,
                            slug=unique_slug,
                            description=desc,
                            content=f"Imported from curated source.\\n\\nURL: {canonical_url}",
                            is_official=True,
                            is_verified=True,
                            category_id=category_id,
                            url=canonical_url,
                        )
                        db.add(new_skill)
                        created_count += 1

                    category_distribution[category_slug] = category_distribution.get(category_slug, 0) + 1

                raw.parsed_data = {
                    "candidate_count": len(candidates),
                    "deduped_count": len(seen_urls),
                    "extracted_count": created_count,
                    "updated_count": updated_count,
                    "skipped_non_skill_count": skipped_non_skill_count,
                    "category_distribution": category_distribution,
                }
                print(f"Upserted from {raw.source_id}: created={created_count}, updated={updated_count}")
            else:
                parsed = parse_skill_md(content)
                raw.parsed_data = parsed

            raw.parse_error = None
            raw.parse_status = "processed"
            # Session is configured with autoflush=False; flush per raw item to avoid
            # cross-source duplicate inserts being invisible until final commit.
            await db.flush()

        except Exception as e:
            print(f"Error parsing raw skill {raw.id}: {e}")
            raw.parse_status = "error"
            raw.parse_error = {"message": str(e)}
            
    await db.commit()

async def run():
    """Run ingest and parse workflow."""
    async with AsyncSessionLocal() as db:
        await ingest_raw(db)
        await parse_queued_raw_skills(db)

if __name__ == "__main__":
    asyncio.run(run())
