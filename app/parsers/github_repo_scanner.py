"""GitHub Repo Scanner."""

import fnmatch
import re
from typing import Any, Optional

from app.ingest.http import get_http_client
from app.settings import get_settings

settings = get_settings()

SKILL_PATH_GLOBS = [
    "skills/*/SKILL.md",
    ".claude/skills/*/SKILL.md",
]
SKILL_KEYWORDS = {
    "skill",
    "skills",
    "claude skill",
    "skills marketplace",
    "agent skills",
    "codex skill",
}
NOISE_PREFIXES = (
    "src/",
    "app/",
    "backend/",
    "frontend/",
    "server/",
    "client/",
)
NOISE_FILES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
}
REPO_URL_PATTERN = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/?.*", re.IGNORECASE)


def extract_repo_full_name(url: str | None) -> Optional[str]:
    """Extract owner/repo from a GitHub URL."""
    if not url:
        return None
    match = REPO_URL_PATTERN.match(url)
    if not match:
        return None
    owner = (match.group(1) or "").strip()
    repo = (match.group(2) or "").strip()
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"

def _matches_allowed_glob(path: str, allowed_path_globs: Optional[list[str]]) -> bool:
    if not allowed_path_globs:
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in allowed_path_globs)


def _matches_skill_layout(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in SKILL_PATH_GLOBS)


def _compute_repo_focus(
    repo_full_name: str,
    repo_description: str,
    blob_paths: list[str],
) -> dict[str, Any]:
    skill_files = [p for p in blob_paths if p.lower().endswith("/skill.md") or p.lower() == "skill.md"]
    canonical_skill_files = [p for p in skill_files if _matches_skill_layout(p)]
    noise_markers = 0
    for path in blob_paths:
        lowered = path.lower()
        if lowered in NOISE_FILES or any(lowered.startswith(prefix) for prefix in NOISE_PREFIXES):
            noise_markers += 1

    repo_text = f"{repo_full_name} {repo_description}".lower()
    keyword_hits = sum(1 for keyword in SKILL_KEYWORDS if keyword in repo_text)
    total_files = max(len(blob_paths), 1)
    canonical_ratio = len(canonical_skill_files) / max(len(skill_files), 1)

    score = 0
    if len(canonical_skill_files) >= 5:
        score += 45
    elif len(canonical_skill_files) >= 2:
        score += 32
    elif len(canonical_skill_files) >= 1:
        score += 15

    if canonical_ratio >= 0.8 and skill_files:
        score += 22
    elif canonical_ratio >= 0.5 and skill_files:
        score += 10

    score += min(keyword_hits * 6, 18)

    # Penalize app-heavy repositories with only incidental skill folders.
    if noise_markers >= 8:
        score -= 35
    elif noise_markers >= 4:
        score -= 18

    if total_files > 1500 and len(canonical_skill_files) < 10:
        score -= 20
    elif total_files > 500 and len(canonical_skill_files) < 5:
        score -= 10

    score = max(0, min(100, score))

    if len(canonical_skill_files) == 0:
        repo_type = "not_skills"
    elif score >= 70:
        repo_type = "skills_only"
    elif score >= 45:
        repo_type = "skills_focused"
    else:
        repo_type = "mixed"

    return {
        "repo_type": repo_type,
        "repo_intent_score": score,
        "total_files": total_files,
        "skill_file_count": len(skill_files),
        "canonical_skill_file_count": len(canonical_skill_files),
        "noise_marker_count": noise_markers,
        "keyword_hits": keyword_hits,
    }


async def list_repo_skills_candidates(
    repo_full_name: str,
    *,
    allowed_path_globs: Optional[list[str]] = None,
    min_repo_type: str = "skills_only",
) -> list[dict[str, Any]]:
    """
    Scan a GitHub repo for SKILL.md files.
    Uses GitHub API Tree/Search.
    """
    client = await get_http_client()
    try:
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

        blob_paths: list[str] = [str(f.get("path", "")) for f in files if f.get("type") == "blob" and f.get("path")]
        focus = _compute_repo_focus(
            repo_full_name=repo_full_name,
            repo_description=(repo_data.get("description") or ""),
            blob_paths=blob_paths,
        )

        type_rank = {"not_skills": 0, "mixed": 1, "skills_focused": 2, "skills_only": 3}
        current_rank = type_rank.get(focus["repo_type"], 0)
        required_rank = type_rank.get(min_repo_type, 3)
        if current_rank < required_rank:
            return []

        candidates = []
        for f in files:
            if f.get("type") != "blob":
                continue
            path = str(f.get("path", ""))
            if not path:
                continue
            if not path.lower().endswith("/skill.md") and path.lower() != "skill.md":
                continue
            if not _matches_skill_layout(path):
                continue
            if not _matches_allowed_glob(path, allowed_path_globs):
                continue

            # Construct raw URL:
            # https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
            raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{path}"
            candidates.append(
                {
                    "path": path,
                    "url": raw_url,
                    "sha": f["sha"],
                    "repo_type": focus["repo_type"],
                    "repo_intent_score": focus["repo_intent_score"],
                    "repo_total_files": focus["total_files"],
                    "repo_skill_files": focus["skill_file_count"],
                    "repo_canonical_skill_files": focus["canonical_skill_file_count"],
                }
            )

        candidates.sort(key=lambda item: item["path"])
        return candidates
    finally:
        await client.aclose()
