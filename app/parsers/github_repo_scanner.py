"""GitHub Repo Scanner."""

import asyncio
from typing import Any

from app.ingest.http import get_http_client, fetch_text
from app.settings import get_settings

settings = get_settings()

async def list_repo_skills_candidates(repo_full_name: str) -> list[dict[str, Any]]:
    """
    Scan a GitHub repo for SKILL.md files.
    Uses GitHub API Tree/Search.
    """
    client = await get_http_client()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    
    # 1. Get default branch SHA
    repo_url = f"{settings.github_api_base}/repos/{repo_full_name}"
    resp = await client.get(repo_url, headers=headers)
    if resp.status_code != 200:
        return []
    
    repo_data = resp.json()
    default_branch = repo_data.get("default_branch", "main")
    
    # 2. Get Tree (Recursive)
    tree_url = f"{repo_url}/git/trees/{default_branch}?recursive=1"
    resp = await client.get(tree_url, headers=headers)
    if resp.status_code != 200:
        return []
        
    tree_data = resp.json()
    files = tree_data.get("tree", [])
    
    candidates = []
    for f in files:
        if f["path"].endswith("SKILL.md") or f["path"].endswith("skill.md"):
            # Construct raw URL
            # https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
            raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{f['path']}"
            candidates.append({
                "path": f["path"],
                "url": raw_url,
                "sha": f["sha"]
            })
            
    await client.aclose()
    return candidates
