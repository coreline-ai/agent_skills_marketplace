"""Source ingestion logic."""

import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from app.ingest.http import fetch_text, get_http_client
from app.parsers.github_repo_scanner import extract_repo_full_name, list_repo_skills_candidates
from app.settings import get_settings

settings = get_settings()

# Curated Claude/Codex skill repositories (SKILL.md-based).
SOURCES = [
    {
        "id": "anthropic-official-skills",
        "type": "github_repo",
        "repo_full_name": "anthropics/skills",
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-code-skills-marketplace-daymade",
        "type": "github_repo",
        "repo_full_name": "daymade/claude-code-skills",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-skills-rknall",
        "type": "github_repo",
        "repo_full_name": "rknall/claude-skills",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-skills-marketplace-mhattingpete",
        "type": "github_repo",
        "repo_full_name": "mhattingpete/claude-skills-marketplace",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-code-marketplace-getty104",
        "type": "github_repo",
        "repo_full_name": "getty104/claude-code-marketplace",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-skills-jamie-bitflight",
        "type": "github_repo",
        "repo_full_name": "Jamie-BitFlight/claude_skills",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "hf-skills",
        "type": "github_repo",
        "repo_full_name": "huggingface/skills",
        "allowed_path_globs": ["skills/*/SKILL.md", ".claude/skills/*/SKILL.md"],
        "min_repo_type": "skills_focused",
    },
    {
        "id": "claude-marketplaces-directory",
        "type": "web_directory",
        "url": "https://claudemarketplaces.com/",
        "max_repos": 60,
        "max_sitemap_pages": 0,
        # Directory sources can include normal project repos with `.claude/skills`.
        # To avoid ingesting project-local skill bundles as marketplace items, we only
        # discover canonical `skills/*/SKILL.md` layout from directory sources.
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_only",
    },
    {
        "id": "skillsforge-directory",
        "type": "web_directory",
        "url": "https://skillsforge.dev/",
        "max_repos": 60,
        "max_sitemap_pages": 0,
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_only",
    },
    {
        "id": "skillsdir-directory",
        "type": "web_directory",
        "url": "https://skillsdir.dev/",
        "max_repos": 60,
        "max_sitemap_pages": 80,
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_only",
    },
    {
        "id": "claude-code-marketplace-directory",
        "type": "web_directory",
        "url": "https://claudecodemarketplace.net/",
        "max_repos": 60,
        "max_sitemap_pages": 80,
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_only",
    },
    {
        "id": "github-search-skillmd",
        "type": "github_search",
        "search_mode": "code",
        # Token is strongly recommended for rate limits, but we allow a tiny unauthenticated
        # discovery budget so the system still "works" out of the box.
        "require_token": False,
        "queries": [
            "filename:SKILL.md path:skills",
            "filename:SKILL.md path:.claude/skills",
        ],
        "max_repos": 80,
        "max_pages": 2,
        "per_page": 50,
        # Global search also matches normal application repos. Keep discovery limited
        # to canonical marketplace layout to avoid pulling project-local `.claude/skills`.
        "allowed_path_globs": ["skills/*/SKILL.md"],
        "min_repo_type": "skills_only",
    },
]

GITHUB_REPO_PATTERN = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:[/?#\"'<>.,;:)\s]|$)",
    re.IGNORECASE,
)
GITHUB_RESERVED_OWNERS = {
    "features",
    "marketplace",
    "orgs",
    "search",
    "settings",
    "topics",
    "collections",
    "sponsors",
    "site",
    "apps",
}
SITEMAP_LOC_PATTERN = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


def _normalize_repo_full_name(owner: str, repo: str) -> Optional[str]:
    owner = (owner or "").strip()
    repo = (repo or "").strip()
    if not owner or not repo:
        return None
    if owner.lower() in GITHUB_RESERVED_OWNERS:
        return None
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def extract_github_repos_from_web_directory(content: str) -> list[str]:
    repos: set[str] = set()
    for match in GITHUB_REPO_PATTERN.finditer(content or ""):
        normalized = _normalize_repo_full_name(match.group(1), match.group(2))
        if normalized:
            repos.add(normalized)
    return sorted(repos)


def extract_urls_from_sitemap_xml(content: str) -> list[str]:
    urls: list[str] = []
    for match in SITEMAP_LOC_PATTERN.finditer(content or ""):
        url = (match.group(1) or "").strip()
        if url:
            urls.append(url)
    return urls


async def discover_repos_from_web_directory(
    source: dict[str, Any],
    client,
) -> list[str]:
    """Discover GitHub repositories from a web directory root + sitemap pages."""
    directory_url = source["url"]
    host = urlparse(directory_url).netloc
    repos: set[str] = set()

    root_html = await fetch_text(directory_url, client)
    if root_html:
        repos.update(extract_github_repos_from_web_directory(root_html))

    sitemap_url = source.get("sitemap_url") or urljoin(directory_url, "/sitemap.xml")
    max_sitemap_pages = int(source.get("max_sitemap_pages", 80))
    if not sitemap_url or max_sitemap_pages <= 0:
        return sorted(repos)

    pending_sitemaps = [sitemap_url]
    visited_sitemaps: set[str] = set()
    visited_pages: set[str] = set()
    page_budget = max_sitemap_pages

    while pending_sitemaps and page_budget > 0:
        current_sitemap = pending_sitemaps.pop(0)
        if current_sitemap in visited_sitemaps:
            continue
        visited_sitemaps.add(current_sitemap)

        xml = await fetch_text(current_sitemap, client)
        if not xml:
            continue

        for loc_url in extract_urls_from_sitemap_xml(xml):
            parsed = urlparse(loc_url)
            if parsed.netloc and parsed.netloc != host:
                continue
            if loc_url.endswith(".xml"):
                if loc_url not in visited_sitemaps:
                    pending_sitemaps.append(loc_url)
                continue
            if loc_url in visited_pages:
                continue
            visited_pages.add(loc_url)
            page_budget -= 1
            if page_budget < 0:
                break

            page_html = await fetch_text(loc_url, client)
            if not page_html:
                continue
            repos.update(extract_github_repos_from_web_directory(page_html))

    return sorted(repos)


def _extract_repo_name_from_search_item(item: dict[str, Any], mode: str) -> Optional[str]:
    if mode == "repositories":
        full_name = (item.get("full_name") or "").strip()
        if full_name and "/" in full_name:
            owner, repo = full_name.split("/", 1)
            return _normalize_repo_full_name(owner, repo)
        html_url = item.get("html_url")
        extracted = extract_repo_full_name(str(html_url) if html_url else None)
        if extracted and "/" in extracted:
            owner, repo = extracted.split("/", 1)
            return _normalize_repo_full_name(owner, repo)
        return None

    repository = item.get("repository") or {}
    full_name = (repository.get("full_name") or "").strip()
    if full_name and "/" in full_name:
        owner, repo = full_name.split("/", 1)
        return _normalize_repo_full_name(owner, repo)

    html_url = repository.get("html_url") or item.get("html_url")
    extracted = extract_repo_full_name(str(html_url) if html_url else None)
    if extracted and "/" in extracted:
        owner, repo = extracted.split("/", 1)
        return _normalize_repo_full_name(owner, repo)
    return None


async def discover_repos_from_github_search(source: dict[str, Any], client) -> list[str]:
    """
    Discover repositories through GitHub Search API, then validate with repo scanner.
    mode=code -> /search/code (recommended: filename/path queries)
    mode=repositories -> /search/repositories
    """
    mode = str(source.get("search_mode", "code")).strip().lower()
    require_token = bool(source.get("require_token", True))
    has_token = bool(settings.github_token)
    if require_token and not has_token:
        print(f"Skipping github_search source '{source.get('id')}' because GITHUB_TOKEN is not configured.")
        return []

    queries = [str(q).strip() for q in source.get("queries", []) if str(q).strip()]
    if not queries:
        return []

    endpoint = "/search/repositories" if mode == "repositories" else "/search/code"
    max_repos = max(1, int(source.get("max_repos", 60)))
    max_pages = max(1, int(source.get("max_pages", 2)))
    per_page = max(1, min(int(source.get("per_page", 50)), 100))

    # Unauthenticated Search API is heavily rate-limited; keep it small.
    if not has_token:
        max_repos = min(max_repos, 20)
        max_pages = min(max_pages, 1)
        per_page = min(per_page, 10)

    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    repos: set[str] = set()
    for query in queries:
        for page in range(1, max_pages + 1):
            params: dict[str, Any] = {"q": query, "per_page": per_page, "page": page}
            if mode == "repositories":
                params["sort"] = "updated"
                params["order"] = "desc"

            search_url = f"{settings.github_api_base}{endpoint}"
            resp = await client.get(search_url, headers=headers, params=params)
            if resp.status_code != 200:
                # 403/429 are common without auth (rate limit / abuse protection).
                detail = ""
                try:
                    j = resp.json() if resp.content else {}
                    if isinstance(j, dict):
                        detail = (j.get("message") or "").strip()
                except Exception:
                    detail = ""
                extra = f" message='{detail}'" if detail else ""
                print(f"GitHub search failed [{resp.status_code}] query='{query}' page={page}{extra}")
                break

            payload = resp.json() if resp.content else {}
            items = payload.get("items", []) or []
            if not items:
                break

            for item in items:
                repo_full_name = _extract_repo_name_from_search_item(item, mode)
                if not repo_full_name:
                    continue
                repos.add(repo_full_name)
                if len(repos) >= max_repos:
                    break

            if len(repos) >= max_repos or len(items) < per_page:
                break

        if len(repos) >= max_repos:
            break

    return sorted(repos)


async def fetch_source_content(source: dict[str, Any]) -> Optional[str]:
    """Fetch content for a source."""
    return await fetch_text(source["url"])


async def run_ingest_sources(progress=None):
    """Fetch all configured sources.

    If provided, `progress` is called with a dict payload describing the current stage.
    It may be a sync or async callable.
    """
    async def _emit(payload: dict) -> None:
        if progress is None:
            return
        try:
            value = progress(payload)
            if hasattr(value, "__await__"):
                await value
        except Exception:
            # Observability must never break ingestion.
            return

    client = await get_http_client()
    results = []
    scanned_repos: set[str] = set()
    
    source_total = len(SOURCES)
    for idx, source in enumerate(SOURCES, start=1):
        source_type = source.get("type", "markdown_list")
        source_id = source["id"]
        await _emit(
            {
                "phase": "ingest_source_start",
                "ingest_source_id": source_id,
                "ingest_source_type": source_type,
                "ingest_source_index": idx,
                "ingest_source_total": source_total,
            }
        )

        if source_type == "github_repo":
            repo_full_name = source["repo_full_name"]
            if repo_full_name.lower() in scanned_repos:
                continue
            scanned_repos.add(repo_full_name.lower())
            try:
                candidates = await list_repo_skills_candidates(
                    repo_full_name,
                    allowed_path_globs=source.get("allowed_path_globs"),
                    min_repo_type=str(source.get("min_repo_type", "skills_focused")),
                )
            except Exception as exc:
                await _emit(
                    {
                        "phase": "ingest_source_error",
                        "ingest_source_id": source_id,
                        "ingest_source_type": source_type,
                        "ingest_source_index": idx,
                        "ingest_source_total": source_total,
                        "ingest_last_source_error": str(exc),
                    }
                )
                continue
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
                        "repo_type": candidate.get("repo_type"),
                        "repo_intent_score": candidate.get("repo_intent_score"),
                        "repo_total_files": candidate.get("repo_total_files"),
                        "repo_skill_files": candidate.get("repo_skill_files"),
                        "repo_canonical_skill_files": candidate.get("repo_canonical_skill_files"),
                    }
                )
            await _emit(
                {
                    "phase": "ingest_source_done",
                    "ingest_source_id": source_id,
                    "ingest_source_type": source_type,
                    "ingest_source_index": idx,
                    "ingest_source_total": source_total,
                }
            )
            continue

        if source_type == "web_directory":
            directory_url = source["url"]
            await _emit(
                {
                    "phase": "ingest_discover_repos",
                    "ingest_source_id": source_id,
                    "ingest_source_type": source_type,
                    "ingest_source_index": idx,
                    "ingest_source_total": source_total,
                    "ingest_directory_url": directory_url,
                }
            )
            try:
                repos = await discover_repos_from_web_directory(source, client)
            except Exception as exc:
                await _emit(
                    {
                        "phase": "ingest_source_error",
                        "ingest_source_id": source_id,
                        "ingest_source_type": source_type,
                        "ingest_source_index": idx,
                        "ingest_source_total": source_total,
                        "ingest_directory_url": directory_url,
                        "ingest_last_source_error": str(exc),
                    }
                )
                continue
            max_repos = int(source.get("max_repos", 60))
            discovered_count = 0

            for repo_full_name in repos:
                if discovered_count >= max_repos:
                    break
                if repo_full_name.lower() in scanned_repos:
                    continue
                scanned_repos.add(repo_full_name.lower())
                discovered_count += 1

                await _emit(
                    {
                        "phase": "ingest_scan_repo",
                        "ingest_source_id": source_id,
                        "ingest_source_type": source_type,
                        "ingest_source_index": idx,
                        "ingest_source_total": source_total,
                        "ingest_repo_full_name": repo_full_name,
                        "ingest_discovered_repo_index": discovered_count,
                        "ingest_discovered_repo_total": min(len(repos), max_repos),
                    }
                )
                try:
                    candidates = await list_repo_skills_candidates(
                        repo_full_name,
                        allowed_path_globs=source.get("allowed_path_globs"),
                        min_repo_type=str(source.get("min_repo_type", "skills_only")),
                    )
                except Exception as exc:
                    await _emit(
                        {
                            "phase": "ingest_source_error",
                            "ingest_source_id": source_id,
                            "ingest_source_type": source_type,
                            "ingest_source_index": idx,
                            "ingest_source_total": source_total,
                            "ingest_repo_full_name": repo_full_name,
                            "ingest_last_source_error": str(exc),
                        }
                    )
                    continue
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
                            "discovered_from": urlparse(directory_url).netloc,
                            "repo_type": candidate.get("repo_type"),
                            "repo_intent_score": candidate.get("repo_intent_score"),
                            "repo_total_files": candidate.get("repo_total_files"),
                            "repo_skill_files": candidate.get("repo_skill_files"),
                            "repo_canonical_skill_files": candidate.get("repo_canonical_skill_files"),
                        }
                    )
            await _emit(
                {
                    "phase": "ingest_source_done",
                    "ingest_source_id": source_id,
                    "ingest_source_type": source_type,
                    "ingest_source_index": idx,
                    "ingest_source_total": source_total,
                    "ingest_discovered_repos": discovered_count,
                }
            )
            continue

        if source_type == "github_search":
            await _emit(
                {
                    "phase": "ingest_github_search",
                    "ingest_source_id": source_id,
                    "ingest_source_type": source_type,
                    "ingest_source_index": idx,
                    "ingest_source_total": source_total,
                }
            )
            try:
                repos = await discover_repos_from_github_search(source, client)
            except Exception as exc:
                await _emit(
                    {
                        "phase": "ingest_source_error",
                        "ingest_source_id": source_id,
                        "ingest_source_type": source_type,
                        "ingest_source_index": idx,
                        "ingest_source_total": source_total,
                        "ingest_last_source_error": str(exc),
                    }
                )
                continue
            max_repos = int(source.get("max_repos", 60))
            discovered_count = 0

            for repo_full_name in repos:
                if discovered_count >= max_repos:
                    break
                if repo_full_name.lower() in scanned_repos:
                    continue
                scanned_repos.add(repo_full_name.lower())
                discovered_count += 1

                await _emit(
                    {
                        "phase": "ingest_scan_repo",
                        "ingest_source_id": source_id,
                        "ingest_source_type": source_type,
                        "ingest_source_index": idx,
                        "ingest_source_total": source_total,
                        "ingest_repo_full_name": repo_full_name,
                        "ingest_discovered_repo_index": discovered_count,
                        "ingest_discovered_repo_total": min(len(repos), max_repos),
                    }
                )
                try:
                    candidates = await list_repo_skills_candidates(
                        repo_full_name,
                        allowed_path_globs=source.get("allowed_path_globs"),
                        min_repo_type=str(source.get("min_repo_type", "skills_only")),
                    )
                except Exception as exc:
                    await _emit(
                        {
                            "phase": "ingest_source_error",
                            "ingest_source_id": source_id,
                            "ingest_source_type": source_type,
                            "ingest_source_index": idx,
                            "ingest_source_total": source_total,
                            "ingest_repo_full_name": repo_full_name,
                            "ingest_last_source_error": str(exc),
                        }
                    )
                    continue
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
                            "discovered_from": f"github_search:{source_id}",
                            "repo_type": candidate.get("repo_type"),
                            "repo_intent_score": candidate.get("repo_intent_score"),
                            "repo_total_files": candidate.get("repo_total_files"),
                            "repo_skill_files": candidate.get("repo_skill_files"),
                            "repo_canonical_skill_files": candidate.get("repo_canonical_skill_files"),
                        }
                    )
            await _emit(
                {
                    "phase": "ingest_source_done",
                    "ingest_source_id": source_id,
                    "ingest_source_type": source_type,
                    "ingest_source_index": idx,
                    "ingest_source_total": source_total,
                    "ingest_discovered_repos": discovered_count,
                }
            )
            continue

        await _emit(
            {
                "phase": "ingest_fetch_url",
                "ingest_source_id": source_id,
                "ingest_source_type": source_type,
                "ingest_source_index": idx,
                "ingest_source_total": source_total,
                "ingest_url": source.get("url"),
            }
        )
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
        await _emit(
            {
                "phase": "ingest_source_done",
                "ingest_source_id": source_id,
                "ingest_source_type": source_type,
                "ingest_source_index": idx,
                "ingest_source_total": source_total,
            }
        )
            
    await client.aclose()
    return results
