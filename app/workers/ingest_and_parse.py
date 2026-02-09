"""Ingest and Parse Worker."""

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from urllib.parse import urlparse

from app.db.session import AsyncSessionLocal
from app.ingest.sources import run_ingest_sources
from app.ingest.db_upsert import upsert_raw_skill
from app.models.raw_skill import RawSkill
from app.parsers.skillmd_parser import parse_skill_md
from app.quality.skill_quality import validate_skill_md
from app.quality.claude_skill_spec import validate_claude_skill_frontmatter
from app.llm.glm_client import summarize_skill_overview, summarize_skill_detail_overview
from app.quality.security_scan import heuristic_security_scan
from app.llm.glm_client import classify_skill_security
from app.settings import get_settings
from app.repos.system_setting_repo import _get_skill_validation_settings_value
from app.repos.system_setting_repo import get_worker_status_value, set_worker_status_value

DEPRECATED_CATEGORY_SLUGS = {"chat", "code", "writing"}

CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("robotics", ["robot", "robotic", "ros", "embodied", "drone", "autonomous vehicle"]),
    ("memory", ["memory", "long-term", "vector store", "context window", "recall"]),
    ("research", ["research", "paper", "literature", "analysis", "experiment", "arxiv"]),
    ("coding", ["code", "developer", "programming", "debug", "refactor", "ide", "repo", "pull request"]),
    ("frameworks", ["framework", "sdk", "library", "orchestr", "multi-agent", "agent runtime"]),
    # "chat", "code", "writing" categories are deprecated; we treat those signals as Tools.
    ("tools", ["tool", "plugin", "extension", "cli", "assistant", "automation utility", "chat", "conversation", "chatbot", "writing", "copywriting", "blog", "content generation", "summarize"]),
    ("data", ["data", "etl", "sql", "analytics", "dataset", "pipeline"]),
    ("productivity", ["productivity", "workflow", "task", "calendar", "notes"]),
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
ALLOWED_REPO_TYPES = {"skills_only", "skills_focused"}
MIN_REPO_INTENT_SCORE = 45

MARKDOWN_BULLET_LINK_PATTERN = re.compile(
    r"^\s*[-*]\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s*(?:[-:–—]\s*(.+))?$"
)
MARKDOWN_HEADER_LINK_PATTERN = re.compile(
    r"^\s*#{2,4}\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s*$"
)
GENERIC_GITHUB_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((https?://github\.com/[^)\s]+)\)"
)

_GITHUB_BLOB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)$"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _patch_worker_status(patch: dict) -> None:
    """Best-effort: update worker heartbeat while ingest/parse is running."""
    try:
        async with AsyncSessionLocal() as db:
            current = await get_worker_status_value(db)
            current_dict = current if isinstance(current, dict) else {}
            merged = current_dict | patch
            now = _utc_now_iso()
            merged["heartbeat_at"] = now

            prev_phase = current_dict.get("phase")
            next_phase = merged.get("phase")
            has_error = bool(patch.get("last_error") or patch.get("ingest_last_source_error"))
            phase_changed = ("phase" in patch) and (next_phase != prev_phase)
            if phase_changed or has_error:
                events = merged.get("recent_events")
                if not isinstance(events, list):
                    events = []
                event = {"at": now, "phase": next_phase or "unknown"}
                for key in (
                    "ingest_source_id",
                    "ingest_source_type",
                    "ingest_source_index",
                    "ingest_source_total",
                    "ingest_directory_url",
                    "ingest_repo_full_name",
                    "ingest_discovered_repo_index",
                    "ingest_discovered_repo_total",
                    "ingest_last_source_error",
                ):
                    value = merged.get(key)
                    if value is not None and value != "":
                        event[key] = value
                events.append(event)
                merged["recent_events"] = events[-50:]

            await set_worker_status_value(db, merged)
            await db.commit()
    except Exception:
        return


def _extract_tag_slugs(metadata: dict) -> list[str]:
    """Extract normalized tag slugs from SKILL.md frontmatter."""
    if not isinstance(metadata, dict):
        return []

    raw = metadata.get("tags") or metadata.get("tag") or metadata.get("keywords")
    values: list[str] = []
    if isinstance(raw, str):
        # "a, b, c" or "a b c"
        parts = re.split(r"[,/|]", raw)
        values.extend([p.strip() for p in parts if p and p.strip()])
    elif isinstance(raw, list):
        for v in raw:
            if isinstance(v, str) and v.strip():
                values.append(v.strip())

    slugs = []
    for v in values:
        slug = slugify_text(v)
        if slug:
            slugs.append(slug)
    # de-dupe, stable
    return sorted(set(slugs))


async def _ensure_skill_source_link(
    db: AsyncSession,
    *,
    skill_id,
    source_id,
    url: str,
    link_type: str = "definition",
) -> None:
    """Create a SkillSourceLink row if missing."""
    from app.models.skill_source_link import SkillSourceLink
    if not skill_id or not source_id or not url:
        return

    existing = (
        await db.execute(
            select(SkillSourceLink)
            .where(
                SkillSourceLink.skill_id == skill_id,
                SkillSourceLink.source_id == source_id,
                SkillSourceLink.external_id == url,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(
        SkillSourceLink(
            skill_id=skill_id,
            source_id=source_id,
            external_id=url,
            link_type=link_type,
        )
    )
    await db.flush()


async def _ensure_skill_tags(db: AsyncSession, *, skill_id, tag_slugs: list[str]) -> None:
    """Add tags (does not delete existing tags)."""
    if not skill_id or not tag_slugs:
        return

    from app.models.tag import Tag
    from app.models.skill_tag import SkillTag

    # Load existing tag rows
    existing_tags = (
        await db.execute(select(Tag).where(Tag.slug.in_(tag_slugs)))
    ).scalars().all()
    tag_by_slug = {t.slug: t for t in existing_tags}

    # Create missing tags
    for slug in tag_slugs:
        if slug in tag_by_slug:
            continue
        tag = Tag(name=slug, slug=slug)
        db.add(tag)
        await db.flush()
        tag_by_slug[slug] = tag

    # Load existing associations for this skill
    existing_assoc = (
        await db.execute(select(SkillTag.tag_id).where(SkillTag.skill_id == skill_id))
    ).scalars().all()
    existing_tag_ids = set(existing_assoc)

    for slug in tag_slugs:
        tag = tag_by_slug.get(slug)
        if not tag or tag.id in existing_tag_ids:
            continue
        db.add(SkillTag(skill_id=skill_id, tag_id=tag.id))
    await db.flush()


def classify_category_slug(name: str, description: str) -> str:
    """Return a normalized category slug based on keyword heuristics."""
    haystack = f"{name} {description}".lower()
    for slug, keywords in CATEGORY_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return normalize_category_slug(slug)
    return "tools"


def normalize_category_slug(slug: str) -> str:
    """Map deprecated categories into Tools to keep taxonomy stable."""
    raw = (slug or "").strip().lower()
    if raw in DEPRECATED_CATEGORY_SLUGS:
        return "tools"
    return raw or "tools"


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


def normalize_to_raw_github_url(url: str) -> str:
    """Convert github.com blob URLs to raw.githubusercontent.com URLs (best effort)."""
    raw = (url or "").strip()
    if not raw:
        return raw
    if "raw.githubusercontent.com" in raw:
        return raw
    m = _GITHUB_BLOB_URL_RE.match(raw)
    if not m:
        return raw
    owner = m.group("owner")
    repo = m.group("repo")
    branch = m.group("branch")
    path = m.group("path")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def normalize_skill_source_url(url: str) -> Optional[str]:
    """Normalize a skill document URL to a stable GitHub page URL."""
    raw = (url or "").strip()
    if not raw.lower().startswith(("http://", "https://")):
        return None

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]
    if "raw.githubusercontent.com" in host:
        # /{owner}/{repo}/{branch}/{path...}
        if len(parts) < 4:
            return None
        owner, repo, branch = parts[0], parts[1], parts[2]
        file_path = "/".join(parts[3:])
        return f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"
    if "github.com" in host:
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]

        # Preserve already-canonical file URLs.
        # Example:
        # https://github.com/{owner}/{repo}/blob/{branch}/skills/{id}/SKILL.md
        if len(parts) >= 5 and parts[2].lower() == "blob":
            branch = parts[3]
            file_path = "/".join(parts[4:])
            return f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"

        # Best-effort conversion when the source points to a file page under /tree/.
        # (Some crawlers may provide tree URLs even for files.)
        if len(parts) >= 5 and parts[2].lower() == "tree":
            branch = parts[3]
            file_path = "/".join(parts[4:])
            if file_path.lower().endswith("skill.md"):
                return f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"

        # Fallback: repo root URL.
        return f"https://github.com/{owner}/{repo}"
    return None


def is_skill_md_source_url(url: Optional[str]) -> bool:
    """Check whether the raw source points to a SKILL.md document."""
    if not url:
        return False
    return urlparse(url).path.lower().endswith("/skill.md")


def is_canonical_skill_doc_url(url: str) -> bool:
    """Allow only canonical Claude/Codex skill paths."""
    path = urlparse(url).path.lower()
    return bool(
        re.search(r"/blob/[^/]+/skills/[^/]+/skill\.md$", path)
        or re.search(r"/blob/[^/]+/\.claude/skills/[^/]+/skill\.md$", path)
    )


def should_accept_repo_metadata(parsed_data: Optional[dict]) -> tuple[bool, str]:
    """Decide whether a raw item came from a trusted skills repository."""
    if not isinstance(parsed_data, dict):
        return True, "legacy_no_repo_metadata"

    repo_type = parsed_data.get("repo_type")
    if isinstance(repo_type, str) and repo_type and repo_type not in ALLOWED_REPO_TYPES:
        return False, f"untrusted_repo_type:{repo_type}"

    score_value = parsed_data.get("repo_intent_score")
    if isinstance(score_value, (int, float)) and float(score_value) < MIN_REPO_INTENT_SCORE:
        return False, f"low_repo_intent_score:{int(score_value)}"

    canonical_files = parsed_data.get("repo_canonical_skill_files")
    if isinstance(canonical_files, int) and canonical_files < 1:
        return False, "no_canonical_skill_files"

    return True, "trusted"


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
        # Claude spec: if name is omitted, the directory name is used.
        # Keep it as-is (no title-casing) for alignment; the UI can prettify if needed.
        if folder_name:
            return folder_name.strip()

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

async def ingest_raw(db: AsyncSession, source_ids: Optional[list[str]] = None) -> int:
    """Fetch from sources and upsert raw skills."""
    await _patch_worker_status({"phase": "ingest_fetch_sources"})
    print("Fetching sources...")
    results = await run_ingest_sources(progress=_patch_worker_status, source_ids=source_ids)
    await _patch_worker_status({"phase": "ingest_upsert_raw", "ingest_results": int(len(results))})
    
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
                "repo_type": res.get("repo_type"),
                "repo_intent_score": res.get("repo_intent_score"),
                "repo_total_files": res.get("repo_total_files"),
                "repo_skill_files": res.get("repo_skill_files"),
                "repo_canonical_skill_files": res.get("repo_canonical_skill_files"),
                "discovered_from": res.get("discovered_from"),
            },
        )
        count += 1
        if count % 100 == 0:
            await _patch_worker_status(
                {
                    "phase": "ingest_upsert_raw",
                    "ingested_so_far": int(count),
                    "ingest_results": int(len(results)),
                }
            )
        
    print(f"Ingested {count} raw items.")
    await _patch_worker_status({"phase": "ingest_done", "last_ingested_raw_items": int(count)})
    return count



async def parse_queued_raw_skills(db: AsyncSession) -> dict:
    """Process pending raw skills."""
    print("Processing pending raw skills...")
    from sqlalchemy import func
    pending_before = (
        await db.execute(select(func.count()).select_from(RawSkill).where(RawSkill.parse_status == "pending"))
    ).scalar_one()
    await _patch_worker_status({"phase": "parse_batch", "pending_before": int(pending_before or 0)})
    # Drain faster than ingestion. This is bounded to avoid runaway CPU/DB time per loop.
    # If this is too heavy for prod, make it a runtime setting in system_settings.
    # NOTE: We prefer draining a backlog quickly once it exists, but keep this
    # bounded so a single batch doesn't monopolize the worker.
    stmt = (
        select(RawSkill)
        .where(RawSkill.parse_status == "pending")
        .order_by(RawSkill.created_at.asc())
        .limit(2000)
    )
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
        or next(iter(category_id_by_slug.values()), None)
    )
    
    # Load runtime validation policy once per batch.
    settings = get_settings()
    profile = str(getattr(settings, "skill_validation_profile", "lax") or "lax")
    enforce = bool(getattr(settings, "skill_validation_enforce", False))
    try:
        row_value = await _get_skill_validation_settings_value(db)
        if isinstance(row_value, dict):
            profile = str(row_value.get("profile") or profile)
            enforce = bool(row_value.get("enforce"))
    except Exception:
        # system_settings table might not exist yet.
        pass

    processed = 0
    errors = 0

    for raw in pending_skills:
        try:
            print(f"DEBUG: Processing RawSkill {raw.id} | URL: '{raw.source_url}'")

            content = raw.content or ""
            ingest_meta = raw.parsed_data if isinstance(raw.parsed_data, dict) else {}
            if not is_skill_md_source_url(raw.source_url):
                raw.parsed_data = {
                    **ingest_meta,
                    "source_type": "unsupported",
                    "reason": "non_skill_md_source",
                }
                raw.parse_error = None
                raw.parse_status = "processed"
                await db.flush()
                processed += 1
                continue

            trusted_repo, reject_reason = should_accept_repo_metadata(ingest_meta)
            if not trusted_repo:
                raw.parsed_data = {
                    **ingest_meta,
                    "source_type": "unsupported",
                    "reason": reject_reason,
                }
                raw.parse_error = None
                raw.parse_status = "processed"
                await db.flush()
                processed += 1
                continue

            if is_skill_md_source_url(raw.source_url):
                parsed = parse_skill_md(content)
                metadata = parsed.get("metadata") or {}
                body = parsed.get("content") or ""
                frontmatter_raw = parsed.get("frontmatter_raw")
                frontmatter_error = parsed.get("frontmatter_error")
                source_url = raw.source_url or ""
                canonical_url = normalize_skill_source_url(source_url) or source_url
                canonical_repo_url = normalize_github_repo_url(source_url) or canonical_url
                if not is_canonical_skill_doc_url(canonical_url):
                    raw.parsed_data = {
                        **ingest_meta,
                        "source_type": "unsupported",
                        "reason": "non_canonical_skill_layout",
                    }
                    raw.parse_error = None
                    raw.parse_status = "processed"
                    await db.flush()
                    processed += 1
                    continue

                spec_result = validate_claude_skill_frontmatter(
                    metadata=metadata,
                    body=body,
                    canonical_url=canonical_url,
                    frontmatter_raw=frontmatter_raw,
                    frontmatter_error=frontmatter_error,
                    profile=profile,
                )
                # Always compute strict result for observability (but don't block unless enforce+profile=strict).
                strict_result = validate_claude_skill_frontmatter(
                    metadata=metadata,
                    body=body,
                    canonical_url=canonical_url,
                    frontmatter_raw=frontmatter_raw,
                    frontmatter_error=frontmatter_error,
                    profile="strict",
                )

                # Use existing derivation for human-friendly name/description, but keep spec-derived too.
                name = derive_skill_name(metadata, source_url, canonical_url)
                description = derive_skill_description(metadata, body)
                tag_slugs = _extract_tag_slugs(metadata)

                # Security scan: block obvious hacking / malicious instructions.
                # This is enforced during parsing so "bad" SKILL.md never becomes a Skill row.
                security_enabled = bool(getattr(settings, "security_scan_enabled", True))
                security_enforce = bool(getattr(settings, "security_scan_enforce", True))
                security_threshold = float(getattr(settings, "security_scan_confidence_threshold", 0.7) or 0.7)
                glm_on_suspicion_only = bool(
                    getattr(settings, "security_scan_glm_on_suspicion_only", True)
                )

                security_input_text = "\n".join([name or "", description or "", body or ""])
                heuristic = heuristic_security_scan(
                    name=name or "",
                    description=description or "",
                    content=security_input_text,
                    url=canonical_url,
                )

                glm_result = None
                if security_enabled and (not glm_on_suspicion_only or heuristic.block):
                    glm_result = await classify_skill_security(
                        name=name or "",
                        description=description or "",
                        content=body or "",
                        url=canonical_url,
                    )

                # Merge decision: heuristic is hard-block for critical, GLM can confirm/override.
                block = False
                block_reasons: list[str] = []
                block_indicators: list[str] = []
                block_severity = "low"
                block_confidence = 0.0

                if heuristic.block:
                    block = True
                    block_severity = heuristic.severity
                    block_confidence = heuristic.confidence
                    block_reasons.extend(heuristic.reasons)
                    block_indicators.extend(heuristic.indicators)

                if isinstance(glm_result, dict):
                    glm_block = bool(glm_result.get("block"))
                    glm_conf = glm_result.get("confidence")
                    try:
                        glm_conf_f = float(glm_conf) if glm_conf is not None else 0.0
                    except Exception:
                        glm_conf_f = 0.0
                    glm_sev = str(glm_result.get("severity") or "").strip().lower() or "low"
                    glm_reasons = glm_result.get("reasons") if isinstance(glm_result.get("reasons"), list) else []
                    glm_inds = glm_result.get("indicators") if isinstance(glm_result.get("indicators"), list) else []

                    if glm_block and glm_conf_f >= security_threshold:
                        block = True
                        block_severity = glm_sev
                        block_confidence = max(block_confidence, glm_conf_f)
                        block_reasons.extend([str(r) for r in glm_reasons if str(r).strip()])
                        block_indicators.extend([str(i) for i in glm_inds if str(i).strip()])
                    elif not glm_block and heuristic.severity != "critical":
                        # Allow GLM to downgrade non-critical heuristic hits (reduce false positives).
                        block = False

                ingest_meta = raw.parsed_data if isinstance(raw.parsed_data, dict) else {}
                ingest_meta = {
                    **ingest_meta,
                    "security_scan": {
                        "heuristic": {
                            "ok": heuristic.ok,
                            "severity": heuristic.severity,
                            "confidence": heuristic.confidence,
                            "reasons": heuristic.reasons,
                            "indicators": heuristic.indicators,
                            "content_sha1": heuristic.content_sha1,
                        },
                        "glm": glm_result,
                        "decision": {
                            "block": bool(block),
                            "severity": block_severity,
                            "confidence": float(block_confidence),
                            "reasons": sorted({r.strip() for r in block_reasons if str(r).strip()}),
                            "indicators": sorted({i.strip() for i in block_indicators if str(i).strip()}),
                        },
                    },
                }

                if security_enabled and security_enforce and block:
                    raw.parsed_data = {
                        **ingest_meta,
                        "source_type": "skill_md",
                        "name": name,
                        "reason": "security_block",
                    }
                    raw.parse_status = "error"
                    raw.parse_error = {
                        "type": "security",
                        "severity": block_severity,
                        "confidence": float(block_confidence),
                        "errors": sorted({r.strip() for r in block_reasons if str(r).strip()}),
                        "indicators": sorted({i.strip() for i in block_indicators if str(i).strip()}),
                    }
                    await db.flush()
                    errors += 1
                    continue

                quality = validate_skill_md(
                    metadata=metadata,
                    body=body,
                    frontmatter_raw=frontmatter_raw,
                    frontmatter_error=frontmatter_error,
                )
                # ingest_meta already merged with security scan above
                ingest_meta = ingest_meta if isinstance(ingest_meta, dict) else {}

                # Store spec validation output for admin review / gradual rollout.
                ingest_meta = {
                    **ingest_meta,
                    "claude_spec": {
                        "profile": profile,
                        "ok": spec_result.ok,
                        "errors": spec_result.errors,
                        "warnings": spec_result.warnings,
                        "normalized": spec_result.normalized,
                        "derived_name": spec_result.derived_name,
                        "derived_description": spec_result.derived_description,
                    },
                    "claude_spec_strict": {
                        "ok": strict_result.ok,
                        "errors": strict_result.errors,
                        "warnings": strict_result.warnings,
                    },
                }

                if enforce and not spec_result.ok:
                    raw.parsed_data = {
                        **ingest_meta,
                        "source_type": "skill_md",
                        "name": name,
                        "quality": {
                            "ok": False,
                            "score": quality.score,
                            "errors": quality.errors,
                            "warnings": quality.warnings,
                        },
                    }
                    raw.parse_status = "error"
                    raw.parse_error = {"type": "claude_spec", "errors": spec_result.errors}
                    await db.flush()
                    errors += 1
                    continue

                if not quality.ok:
                    raw.parsed_data = {
                        **ingest_meta,
                        "source_type": "skill_md",
                        "name": name,
                        "quality": {
                            "ok": False,
                            "score": quality.score,
                            "errors": quality.errors,
                            "warnings": quality.warnings,
                        },
                    }
                    raw.parse_status = "error"
                    raw.parse_error = {"type": "quality", "errors": quality.errors}
                    await db.flush()
                    errors += 1
                    continue

                category_slug = None
                raw_category = metadata.get("category")
                if isinstance(raw_category, str) and raw_category.strip():
                    category_slug = normalize_category_slug(slugify_text(raw_category))
                if not category_slug:
                    category_slug = normalize_category_slug(classify_category_slug(name, description))
                category_id = category_id_by_slug.get(category_slug, fallback_category_id)

                existing_skill = (
                    await db.execute(select(Skill).where(Skill.url == canonical_url).limit(1))
                ).scalar_one_or_none()
                if not existing_skill and canonical_repo_url and canonical_repo_url != canonical_url:
                    # Backward compatibility: migrate legacy repo-level rows to file-level URL.
                    existing_skill = (
                        await db.execute(
                            select(Skill)
                            .where(Skill.url == canonical_repo_url, Skill.name == name)
                            .limit(1)
                        )
                    ).scalar_one_or_none()
                    if existing_skill:
                        existing_skill.url = canonical_url
                if existing_skill:
                    if name:
                        existing_skill.name = name
                    if description:
                        existing_skill.description = description
                    if body:
                        existing_skill.content = body
                    if category_id:
                        existing_skill.category_id = category_id
                    existing_skill.spec = {
                        **(spec_result.normalized or {}),
                        "derived_name": spec_result.derived_name,
                        "derived_description": spec_result.derived_description,
                    }
                    existing_skill.is_official = True
                    existing_skill.is_verified = True
                    created_count = 0
                    updated_count = 1

                    await _ensure_skill_tags(db, skill_id=existing_skill.id, tag_slugs=tag_slugs)
                    await _ensure_skill_source_link(
                        db,
                        skill_id=existing_skill.id,
                        source_id=raw.source_id,
                        url=canonical_url,
                        link_type="definition",
                    )
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
                        summary=None,
                        overview=None,
                        content=body,
                        category_id=category_id,
                        url=canonical_url,
                        spec={
                            **(spec_result.normalized or {}),
                            "derived_name": spec_result.derived_name,
                            "derived_description": spec_result.derived_description,
                        },
                        is_official=True,
                        is_verified=True,
                    )
                    db.add(new_skill)
                    await db.flush()
                    await _ensure_skill_tags(db, skill_id=new_skill.id, tag_slugs=tag_slugs)
                    await _ensure_skill_source_link(
                        db,
                        skill_id=new_skill.id,
                        source_id=raw.source_id,
                        url=canonical_url,
                        link_type="definition",
                    )
                    created_count = 1
                    updated_count = 0

                raw.parsed_data = {
                    **ingest_meta,
                    "source_type": "skill_md",
                    "name": name,
                    "category_slug": category_slug,
                    "quality": {
                        "ok": True,
                        "score": quality.score,
                        "errors": quality.errors,
                        "warnings": quality.warnings,
                    },
                    "extracted_count": created_count,
                    "updated_count": updated_count,
                }
                raw.parse_error = None
                raw.parse_status = "processed"
                await db.flush()
                processed += 1
                continue

        except Exception as e:
            print(f"Error parsing raw skill {raw.id}: {e}")
            raw.parse_status = "error"
            raw.parse_error = {"message": str(e)}
            errors += 1
            
    await db.commit()

    pending_after = (
        await db.execute(select(func.count()).select_from(RawSkill).where(RawSkill.parse_status == "pending"))
    ).scalar_one()

    # Keep counters consistent with the queue delta.
    # `errors` counts rows moved to parse_status="error".
    drained = max(int(pending_before or 0) - int(pending_after or 0), 0)
    processed_effective = max(int(drained) - int(errors), 0)
    await _patch_worker_status(
        {
            "phase": "parse_done",
            "pending_before": int(pending_before or 0),
            "pending_after": int(pending_after or 0),
            "processed": int(processed_effective),
            "errors": int(errors),
            "batch_size": int(len(pending_skills)),
            "drained": int(drained),
        }
    )

    return {
        "pending_before": int(pending_before or 0),
        "pending_after": int(pending_after or 0),
        "processed": int(processed_effective),
        "errors": int(errors),
        "batch_size": int(len(pending_skills)),
        "drained": int(drained),
    }


async def backfill_missing_summaries(db: AsyncSession, *, limit: int = 15) -> int:
    """Fill Skill.summary for existing rows after GLM is configured (bounded to avoid runaway costs)."""
    from app.models.skill import Skill
    from app.llm.glm_client import glm_is_configured

    if limit <= 0 or not glm_is_configured():
        return 0

    stmt = (
        select(Skill)
        .where(Skill.summary.is_(None))
        .order_by(Skill.updated_at.desc())
        .limit(int(limit))
    )
    result = await db.execute(stmt)
    skills = result.scalars().all()

    updated = 0
    for skill in skills:
        name = (skill.name or "").strip()
        description = (skill.description or "").strip()
        content = (skill.content or "").strip()
        if not name or not description:
            continue
        overview = await summarize_skill_overview(
            name=name,
            description=description,
            content=content,
        )
        if overview:
            skill.summary = overview
            updated += 1

    if updated:
        await db.commit()
    return updated


async def backfill_missing_detail_overviews(db: AsyncSession, *, limit: int = 10) -> int:
    """Fill Skill.overview for existing rows after GLM is configured (bounded to avoid runaway costs)."""
    from app.models.skill import Skill
    from app.llm.glm_client import glm_is_configured

    if limit <= 0 or not glm_is_configured():
        return 0

    stmt = (
        select(Skill)
        .where(Skill.overview.is_(None))
        .order_by(Skill.updated_at.desc())
        .limit(int(limit))
    )
    result = await db.execute(stmt)
    skills = result.scalars().all()

    updated = 0
    for skill in skills:
        name = (skill.name or "").strip()
        description = (skill.description or "").strip()
        content = (skill.content or "").strip()
        if not name or not description:
            continue
        detail_overview = await summarize_skill_detail_overview(
            name=name,
            description=description,
            content=content,
        )
        if detail_overview:
            skill.overview = detail_overview
            updated += 1

    if updated:
        await db.commit()
    return updated


async def _get_or_create_direct_url_source_id(db: AsyncSession):
    """A fallback SkillSource to attach SkillSourceLinks when RawSkill lookup fails."""
    from app.models.skill_source import SkillSource

    existing = (
        await db.execute(
            select(SkillSource).where(
                SkillSource.type == "direct_url",
                SkillSource.url == "https://skills-marketplace.local/direct-url",
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing.id
    src = SkillSource(
        name="Direct URL",
        url="https://skills-marketplace.local/direct-url",
        type="direct_url",
        is_active=True,
        description="Fallback source for direct skill URLs (auto-generated).",
    )
    db.add(src)
    await db.flush()
    return src.id


async def backfill_missing_source_links(db: AsyncSession, *, limit: int = 200) -> int:
    """Backfill SkillSourceLink rows for Skills that have a URL but no source links yet."""
    if limit <= 0:
        return 0

    from app.models.skill import Skill
    from app.models.skill_source_link import SkillSourceLink

    missing_link_exists = (
        select(SkillSourceLink.id).where(SkillSourceLink.skill_id == Skill.id).exists()
    )
    stmt = (
        select(Skill)
        .where(Skill.url.is_not(None))
        .where(~missing_link_exists)
        .order_by(Skill.updated_at.desc())
        .limit(int(limit))
    )
    skills = (await db.execute(stmt)).scalars().all()
    if not skills:
        return 0

    direct_source_id = None
    created = 0

    for skill in skills:
        canonical_url = (skill.url or "").strip()
        if not canonical_url:
            continue
        raw_url = normalize_to_raw_github_url(canonical_url)

        raw = (
            await db.execute(
                select(RawSkill).where(
                    (RawSkill.external_id == raw_url) | (RawSkill.source_url == raw_url)
                ).limit(1)
            )
        ).scalar_one_or_none()

        source_id = raw.source_id if raw else None
        if not source_id:
            if direct_source_id is None:
                direct_source_id = await _get_or_create_direct_url_source_id(db)
            source_id = direct_source_id

        await _ensure_skill_source_link(
            db,
            skill_id=skill.id,
            source_id=source_id,
            url=raw_url or canonical_url,
            link_type="definition",
        )
        created += 1

    if created:
        await db.commit()
    return created


async def backfill_missing_tags_from_raw_frontmatter(db: AsyncSession, *, limit: int = 150) -> int:
    """Backfill SkillTag rows from RawSkill frontmatter when present."""
    if limit <= 0:
        return 0

    from app.models.skill import Skill
    from app.models.skill_tag import SkillTag

    has_tags_exists = select(SkillTag.tag_id).where(SkillTag.skill_id == Skill.id).exists()
    stmt = (
        select(Skill)
        .where(Skill.url.is_not(None))
        .where(~has_tags_exists)
        .order_by(Skill.updated_at.desc())
        .limit(int(limit))
    )
    skills = (await db.execute(stmt)).scalars().all()
    if not skills:
        return 0

    updated = 0
    for skill in skills:
        canonical_url = (skill.url or "").strip()
        if not canonical_url:
            continue
        raw_url = normalize_to_raw_github_url(canonical_url)
        raw = (
            await db.execute(select(RawSkill).where(RawSkill.external_id == raw_url).limit(1))
        ).scalar_one_or_none()
        if not raw or not raw.content:
            continue

        parsed = parse_skill_md(raw.content)
        metadata = parsed.get("metadata") if isinstance(parsed, dict) else {}
        tag_slugs = _extract_tag_slugs(metadata if isinstance(metadata, dict) else {})
        if not tag_slugs:
            continue

        await _ensure_skill_tags(db, skill_id=skill.id, tag_slugs=tag_slugs)
        updated += 1

    if updated:
        await db.commit()
    return updated


async def backfill_missing_specs_from_raw_frontmatter(db: AsyncSession, *, limit: int = 200) -> int:
    """Backfill Skill.spec from RawSkill frontmatter when present."""
    if limit <= 0:
        return 0

    from app.models.skill import Skill

    stmt = (
        select(Skill)
        .where(Skill.url.is_not(None))
        .where(Skill.spec.is_(None))
        .order_by(Skill.updated_at.desc())
        .limit(int(limit))
    )
    skills = (await db.execute(stmt)).scalars().all()
    if not skills:
        return 0

    updated = 0
    for skill in skills:
        canonical_url = (skill.url or "").strip()
        if not canonical_url:
            continue
        raw_url = normalize_to_raw_github_url(canonical_url)

        raw = (
            await db.execute(
                select(RawSkill).where(
                    (RawSkill.external_id == raw_url)
                    | (RawSkill.source_url == raw_url)
                    | (RawSkill.external_id == canonical_url)
                    | (RawSkill.source_url == canonical_url)
                ).limit(1)
            )
        ).scalar_one_or_none()
        if not raw or not raw.content:
            continue

        parsed = parse_skill_md(raw.content)
        metadata = parsed.get("metadata") if isinstance(parsed, dict) else {}
        body = parsed.get("content") if isinstance(parsed, dict) else ""
        frontmatter_raw = parsed.get("frontmatter_raw") if isinstance(parsed, dict) else None
        frontmatter_error = parsed.get("frontmatter_error") if isinstance(parsed, dict) else None

        spec_result = validate_claude_skill_frontmatter(
            metadata=metadata if isinstance(metadata, dict) else {},
            body=body or "",
            canonical_url=canonical_url,
            frontmatter_raw=frontmatter_raw,
            frontmatter_error=frontmatter_error,
            profile="lax",
        )
        skill.spec = {
            **(spec_result.normalized or {}),
            "derived_name": spec_result.derived_name,
            "derived_description": spec_result.derived_description,
        }
        updated += 1

    if updated:
        await db.commit()
    return updated


async def run(source_ids: Optional[list[str]] = None):
    """Run ingest and parse workflow."""
    async with AsyncSessionLocal() as db:
        ingested = await ingest_raw(db, source_ids=source_ids)
        parse_stats = await parse_queued_raw_skills(db)
        try:
            # Faster convergence: fill existing rows in a few cycles, then this becomes a no-op.
            filled = await backfill_missing_source_links(db, limit=1000)
            if filled:
                print(f"Backfilled {filled} missing source links.")
        except Exception as e:
            print(f"Source link backfill error: {e}")
        try:
            filled = await backfill_missing_tags_from_raw_frontmatter(db, limit=500)
            if filled:
                print(f"Backfilled {filled} missing tags from frontmatter.")
        except Exception as e:
            print(f"Tag backfill error: {e}")
        try:
            filled = await backfill_missing_specs_from_raw_frontmatter(db, limit=500)
            if filled:
                print(f"Backfilled {filled} missing specs from frontmatter.")
        except Exception as e:
            print(f"Spec backfill error: {e}")
        try:
            filled = await backfill_missing_summaries(db, limit=10)
            if filled:
                print(f"Backfilled {filled} missing summaries.")
        except Exception as e:
            # Never fail the worker loop due to optional summary backfill.
            print(f"Summary backfill error: {e}")
        try:
            filled = await backfill_missing_detail_overviews(db, limit=5)
            if filled:
                print(f"Backfilled {filled} missing detail overviews.")
        except Exception as e:
            print(f"Detail overview backfill error: {e}")
    return {
        "ingested": int(ingested or 0),
        "parse": parse_stats if isinstance(parse_stats, dict) else None,
    }

if __name__ == "__main__":
    asyncio.run(run())
