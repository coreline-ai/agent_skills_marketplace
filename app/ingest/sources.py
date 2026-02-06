"""Source ingestion logic."""

from typing import Any, Optional

from app.ingest.http import fetch_text, get_http_client
from app.parsers.github_repo_scanner import list_repo_skills_candidates

# Curated Claude/Codex skill repositories (SKILL.md-based).
SOURCES = [
    {
        "id": "anthropic-official-skills",
        "type": "github_repo",
        "repo_full_name": "anthropics/skills",
    },
    {
        "id": "claude-code-skills-marketplace-daymade",
        "type": "github_repo",
        "repo_full_name": "daymade/claude-code-skills",
    },
    {
        "id": "claude-skills-rknall",
        "type": "github_repo",
        "repo_full_name": "rknall/claude-skills",
    },
    {
        "id": "claude-skills-marketplace-mhattingpete",
        "type": "github_repo",
        "repo_full_name": "mhattingpete/claude-skills-marketplace",
    },
    {
        "id": "claude-code-marketplace-getty104",
        "type": "github_repo",
        "repo_full_name": "getty104/claude-code-marketplace",
    },
    {
        "id": "claude-skills-jamie-bitflight",
        "type": "github_repo",
        "repo_full_name": "Jamie-BitFlight/claude_skills",
    },
    {
        "id": "cc-dev-tools-lucklyric",
        "type": "github_repo",
        "repo_full_name": "Lucklyric/cc-dev-tools",
    },
    {
        "id": "hf-skills",
        "type": "github_repo",
        "repo_full_name": "huggingface/skills",
    },
]

async def fetch_source_content(source: dict[str, Any]) -> Optional[str]:
    """Fetch content for a source."""
    return await fetch_text(source["url"])

async def run_ingest_sources():
    """Fetch all configured sources."""
    client = await get_http_client()
    results = []
    
    for source in SOURCES:
        source_type = source.get("type", "markdown_list")
        source_id = source["id"]

        if source_type == "github_repo":
            repo_full_name = source["repo_full_name"]
            candidates = await list_repo_skills_candidates(repo_full_name)
            for candidate in candidates:
                content = await fetch_text(candidate["url"], client)
                if not content:
                    continue
                results.append(
                    {
                        "source_id": source_id,
                        "content": content,
                        "url": candidate["url"],
                        "external_id": candidate["url"],
                        "source_type": "skill_md",
                        "repo_full_name": repo_full_name,
                        "skill_path": candidate["path"],
                        "skill_sha": candidate["sha"],
                    }
                )
            continue

        content = await fetch_text(source["url"], client)
        if not content:
            continue
        results.append(
            {
                "source_id": source_id,
                "content": content,
                "url": source["url"],
                "external_id": source["url"],
                "source_type": source_type,
            }
        )
            
    await client.aclose()
    return results
