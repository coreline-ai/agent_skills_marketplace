**“자동 수집(ingest) + SKILL.md 파싱 + raw 큐/프리뷰/중복후보 API + 배치 실행”**까지 한 번에 완성본

의존성 추가 (pyproject.toml 업데이트)
0.1 pyproject.toml 의 dependencies에 추가
"PyYAML>=6.0.1",
"beautifulsoup4>=4.12.3",
"rapidfuzz>=3.9.6",
"requests>=2.32.3",

1) Settings 확장 (.env / settings.py)
1.1 .env.example 추가
# GitHub (optional but strongly recommended)
GITHUB_TOKEN=""
GITHUB_API_BASE="https://api.github.com"

# Ingest Sources
AWESOME_LIST_RAW_URL="https://raw.githubusercontent.com/kepano/obsidian-skills/main/README.md"

# If you have a known skills repo (Anthropic etc)
ANTHROPIC_SKILLS_REPO="anthropics/skills"

# Crawler Behavior
INGEST_HTTP_TIMEOUT_SECONDS=20
INGEST_MAX_REPOS_PER_RUN=50
PARSER_MAX_RAW_SKILLS_PER_RUN=200

1.2 app/settings.py 필드 추가
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Agent Skills Marketplace"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 120

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin1234!"

    DATABASE_URL: str

    # GitHub
    GITHUB_TOKEN: str | None = None
    GITHUB_API_BASE: str = "https://api.github.com"

    # Sources
    AWESOME_LIST_RAW_URL: str | None = None
    ANTHROPIC_SKILLS_REPO: str | None = None

    # Ingest limits
    INGEST_HTTP_TIMEOUT_SECONDS: int = 20
    INGEST_MAX_REPOS_PER_RUN: int = 50
    PARSER_MAX_RAW_SKILLS_PER_RUN: int = 200


settings = Settings()

2) Ingest 공통 HTTP 클라이언트
2.1 app/ingest/http.py
import requests
from app.settings import settings


def make_session() -> requests.Session:
    s = requests.Session()
    headers = {"User-Agent": "agent-skills-marketplace/0.1"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github+json"
    s.headers.update(headers)
    return s


def get_text(url: str, timeout: int | None = None) -> str:
    timeout = timeout or settings.INGEST_HTTP_TIMEOUT_SECONDS
    s = make_session()
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

3) GitHub Repo 스캐너 + SKILL.md 다운로드
3.1 app/parsers/github_repo_scanner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import requests

from app.settings import settings
from app.ingest.http import make_session


@dataclass
class SkillFile:
    repo: str              # owner/repo
    path: str              # path in repo
    download_url: str      # raw download url


def _gh_get_json(url: str) -> dict | list:
    s = make_session()
    r = s.get(url, timeout=settings.INGEST_HTTP_TIMEOUT_SECONDS)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


def list_skill_md_candidates(repo_full_name: str) -> list[SkillFile]:
    """
    GitHub Contents API를 사용해 흔한 위치부터 탐색.
    - SKILL.md
    - skills/SKILL.md
    - skills/*/SKILL.md
    - skill/SKILL.md (간혹 있음)
    """
    base = settings.GITHUB_API_BASE.rstrip("/")
    out: list[SkillFile] = []

    # helper: contents
    def contents(path: str) -> list[dict]:
        url = f"{base}/repos/{repo_full_name}/contents/{path}".rstrip("/")
        j = _gh_get_json(url)
        if isinstance(j, list):
            return j
        return []

    # 1) root SKILL.md
    root_items = contents("")
    for it in root_items:
        if it.get("type") == "file" and (it.get("name") or "").lower() == "skill.md":
            out.append(SkillFile(repo=repo_full_name, path=it.get("path"), download_url=it.get("download_url")))
            return out  # root가 있으면 그걸 우선으로

    # 2) skills/SKILL.md or skills/*/SKILL.md
    skills_dir = contents("skills")
    for it in skills_dir:
        if it.get("type") == "file" and (it.get("name") or "").lower() == "skill.md":
            out.append(SkillFile(repo=repo_full_name, path=it.get("path"), download_url=it.get("download_url")))
        if it.get("type") == "dir":
            sub = contents(it.get("path"))
            for s2 in sub:
                if s2.get("type") == "file" and (s2.get("name") or "").lower() == "skill.md":
                    out.append(SkillFile(repo=repo_full_name, path=s2.get("path"), download_url=s2.get("download_url")))

    # 3) skill/SKILL.md
    skill_dir = contents("skill")
    for it in skill_dir:
        if it.get("type") == "file" and (it.get("name") or "").lower() == "skill.md":
            out.append(SkillFile(repo=repo_full_name, path=it.get("path"), download_url=it.get("download_url")))

    return out


def download_file_text(download_url: str) -> str:
    s = make_session()
    r = s.get(download_url, timeout=settings.INGEST_HTTP_TIMEOUT_SECONDS)
    r.raise_for_status()
    return r.text


def detect_repo_capabilities(repo_full_name: str) -> dict:
    """
    repo 루트에 scripts/assets/references/examples 폴더 존재 여부를 대략 확인.
    """
    base = settings.GITHUB_API_BASE.rstrip("/")
    url = f"{base}/repos/{repo_full_name}/contents"
    s = make_session()
    r = s.get(url, timeout=settings.INGEST_HTTP_TIMEOUT_SECONDS)
    if r.status_code != 200:
        return {}
    items = r.json() if isinstance(r.json(), list) else []
    names = {str(i.get("name", "")).lower(): i.get("type") for i in items}
    def has_dir(n: str) -> bool:
        return names.get(n) == "dir"
    return {
        "scripts": has_dir("scripts"),
        "assets": has_dir("assets"),
        "references": has_dir("references"),
        "examples": has_dir("examples"),
    }

4) SKILL.md 파서 (SKILL_PARSER.md 규칙 구현)
4.1 app/parsers/skillmd_parser.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class ParsedSkillDoc:
    parse_status: str
    parse_errors: list[str]
    frontmatter: dict[str, Any] | None
    body_md: str
    normalized: dict[str, Any]


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """
    Frontmatter 경계:
    - 문서 최상단에서 '---' 또는 '===' 같은 구분선으로 시작하면 frontmatter 후보.
    - 다음 동일 계열 구분선까지를 frontmatter로 본다.
    실패하면 frontmatter 없음으로 처리.
    """
    if not text:
        return None, ""

    lines = text.splitlines()
    if not lines:
        return None, ""

    first = lines[0].strip()
    is_fence = (len(first) >= 3 and all(c == "-" for c in first)) or (len(first) >= 3 and all(c == "=" for c in first))
    if not is_fence:
        return None, text

    # find closing fence
    for i in range(1, min(len(lines), 5000)):
        t = lines[i].strip()
        if t and ((len(t) >= 3 and all(c == "-" for c in t)) or (len(t) >= 3 and all(c == "=" for c in t))):
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            return fm, body

    return None, text


def _normalize_tags(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        # comma separated
        parts = [p.strip() for p in v.split(",")]
        return [p for p in parts if p]
    return []


def parse_skill_md(text: str) -> ParsedSkillDoc:
    errors: list[str] = []
    fm_text, body = _split_frontmatter(text)

    frontmatter = None
    status = "markdown_only"

    if fm_text is not None:
        # try yaml
        try:
            frontmatter = yaml.safe_load(fm_text) or {}
            if not isinstance(frontmatter, dict):
                errors.append("yaml_not_mapping")
                frontmatter = {}
        except Exception:
            errors.append("yaml_parse_error")
            frontmatter = {}
            status = "invalid_frontmatter"

    # normalize fields (best effort)
    norm: dict[str, Any] = {}
    if frontmatter is not None:
        name = frontmatter.get("name")
        if isinstance(name, list) and name:
            name = name[0]
        if name is not None and not isinstance(name, str):
            name = str(name)
        if name:
            norm["name"] = name.strip()
        else:
            errors.append("missing_name")

        desc = frontmatter.get("description") or frontmatter.get("summary")
        if desc is not None and not isinstance(desc, str):
            desc = str(desc)
        if desc:
            norm["summary"] = desc.strip()

        norm["tags"] = _normalize_tags(frontmatter.get("tags"))
        cat = frontmatter.get("category")
        if cat is not None and not isinstance(cat, str):
            cat = str(cat)
        if cat:
            norm["category_raw"] = cat.strip()

        # optional fields passthrough
        for k in ["inputs", "outputs", "constraints", "triggers", "tools", "skills", "workflows"]:
            if k in frontmatter:
                norm[k] = frontmatter.get(k)

        # parse_status decision
        if status != "invalid_frontmatter":
            # if 핵심 필드(name) 있고 frontmatter가 dict이면 valid/partial
            if "name" in norm:
                status = "valid" if len(errors) == 0 else "partial"
            else:
                status = "partial"

    # body required check
    if (body or "").strip() == "":
        errors.append("empty_body")

    return ParsedSkillDoc(
        parse_status=status,
        parse_errors=errors,
        frontmatter=frontmatter,
        body_md=body or "",
        normalized=norm,
    )

5) DB Upsert 유틸 (raw_skills 저장/업데이트)
5.1 app/ingest/db_upsert.py
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.raw_skill import RawSkill


def upsert_raw_skill(
    db: Session,
    *,
    source_id,
    external_id: str | None,
    skill_url: str | None,
    name_raw: str | None,
    description_raw: str | None,
    category_raw: str | None,
    tags_raw,
    github_repo: str | None,
    skill_path: str | None,
    license_raw: str | None,
    data_json: dict | None,
    fetch_status: str = "ok",
    source_revision: str | None = None,
    status: str = "new",
):
    """
    UNIQUE(source_id, external_id) 또는 UNIQUE(source_id, skill_url) 충돌을 견딤.
    - 외부에서 external_id가 없으면, skill_url을 최대한 넣어 충돌 기준을 확보.
    - 두 unique가 동시에 걸릴 수 있으니, MVP에서는 (source_id, skill_url) 기반 upsert를 우선.
    """
    values = dict(
        source_id=source_id,
        external_id=external_id,
        skill_url=skill_url,
        name_raw=name_raw,
        description_raw=description_raw,
        category_raw=category_raw,
        tags_raw=tags_raw,
        github_repo=github_repo,
        skill_path=skill_path,
        license_raw=license_raw,
        data_json=data_json,
        fetch_status=fetch_status,
        source_revision=source_revision,
        status=status,
    )

    stmt = pg_insert(RawSkill).values(**values)

    # prefer url conflict target when available
    if skill_url:
        stmt = stmt.on_conflict_do_update(
            constraint="uq_raw_source_url",
            set_={
                "name_raw": stmt.excluded.name_raw,
                "description_raw": stmt.excluded.description_raw,
                "category_raw": stmt.excluded.category_raw,
                "tags_raw": stmt.excluded.tags_raw,
                "github_repo": stmt.excluded.github_repo,
                "skill_path": stmt.excluded.skill_path,
                "license_raw": stmt.excluded.license_raw,
                "data_json": stmt.excluded.data_json,
                "fetch_status": stmt.excluded.fetch_status,
                "source_revision": stmt.excluded.source_revision,
                "status": stmt.excluded.status,
            },
        )
    else:
        stmt = stmt.on_conflict_do_update(
            constraint="uq_raw_source_external",
            set_={
                "skill_url": stmt.excluded.skill_url,
                "name_raw": stmt.excluded.name_raw,
                "description_raw": stmt.excluded.description_raw,
                "category_raw": stmt.excluded.category_raw,
                "tags_raw": stmt.excluded.tags_raw,
                "github_repo": stmt.excluded.github_repo,
                "skill_path": stmt.excluded.skill_path,
                "license_raw": stmt.excluded.license_raw,
                "data_json": stmt.excluded.data_json,
                "fetch_status": stmt.excluded.fetch_status,
                "source_revision": stmt.excluded.source_revision,
                "status": stmt.excluded.status,
            },
        )

    db.execute(stmt)

6) 소스 Ingest 구현 (Awesome 리스트 + Anthropic skills repo)
6.1 app/ingest/sources.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

from app.settings import settings
from app.ingest.http import get_text


@dataclass
class RepoRef:
    repo: str  # owner/repo
    name: str | None = None
    desc: str | None = None
    url: str | None = None


RE_GH_REPO = re.compile(r"(?:https?://github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def parse_awesome_markdown_repos(md: str) -> list[RepoRef]:
    """
    README markdown에서 github repo 링크를 긁어온다.
    - MVP: (owner/repo) 패턴을 전부 수집하고 중복 제거
    """
    found: dict[str, RepoRef] = {}

    # markdown link: [text](url)
    for m in re.finditer(r"\[([^\]]+)\]\((https?://github\.com/[^)]+)\)", md):
        text = m.group(1).strip()
        url = m.group(2).strip()
        mm = RE_GH_REPO.search(url)
        if not mm:
            continue
        repo = f"{mm.group(1)}/{mm.group(2)}"
        if repo not in found:
            found[repo] = RepoRef(repo=repo, name=text, url=url)

    # plain repo mentions
    for m in RE_GH_REPO.finditer(md):
        repo = f"{m.group(1)}/{m.group(2)}"
        if repo not in found:
            found[repo] = RepoRef(repo=repo, url=f"https://github.com/{repo}")

    return list(found.values())


def ingest_awesome_list() -> list[RepoRef]:
    if not settings.AWESOME_LIST_RAW_URL:
        return []
    md = get_text(settings.AWESOME_LIST_RAW_URL)
    repos = parse_awesome_markdown_repos(md)
    return repos[: settings.INGEST_MAX_REPOS_PER_RUN]


def ingest_anthropic_skills_repo() -> list[RepoRef]:
    """
    특정 skills repo를 고정으로 넣어두면,
    그 repo 자체를 스캔해 SKILL.md를 수집한다.
    """
    if not settings.ANTHROPIC_SKILLS_REPO:
        return []
    return [RepoRef(repo=settings.ANTHROPIC_SKILLS_REPO, url=f"https://github.com/{settings.ANTHROPIC_SKILLS_REPO}")]

7) Ingest Runner: raw_skills 채우기 + SKILL.md 파싱까지 한번에
7.1 app/workers/ingest_and_parse.py
from __future__ import annotations

import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.settings import settings
from app.models.skill_source import SkillSource
from app.models.raw_skill import RawSkill

from app.ingest.sources import ingest_awesome_list, ingest_anthropic_skills_repo
from app.ingest.db_upsert import upsert_raw_skill

from app.parsers.github_repo_scanner import list_skill_md_candidates, download_file_text, detect_repo_capabilities
from app.parsers.skillmd_parser import parse_skill_md


def _stable_external_id(source_name: str, repo: str, path: str | None) -> str:
    s = f"{source_name}:{repo}:{path or ''}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:32]


def _ensure_sources(db: Session) -> dict[str, SkillSource]:
    """
    최초 실행 시 소스 레코드 자동 생성
    """
    existing = {s.name: s for s in db.execute(select(SkillSource)).scalars().all()}

    def ensure(name: str, type_: str, base_url: str | None = None, api_url: str | None = None) -> SkillSource:
        if name in existing:
            return existing[name]
        src = SkillSource(name=name, type=type_, base_url=base_url, api_url=api_url, status="active")
        db.add(src)
        db.flush()
        existing[name] = src
        return src

    ensure("awesome_list", "list", base_url=settings.AWESOME_LIST_RAW_URL)
    ensure("anthropic_skills", "github", base_url=f"https://github.com/{settings.ANTHROPIC_SKILLS_REPO}" if settings.ANTHROPIC_SKILLS_REPO else None)
    db.commit()
    return existing


def ingest_raw(db: Session) -> dict:
    sources = _ensure_sources(db)
    awesome_src = sources["awesome_list"]
    anth_src = sources["anthropic_skills"]

    repos = []
    repos.extend(ingest_awesome_list())
    repos.extend(ingest_anthropic_skills_repo())

    inserted = 0
    for r in repos:
        # GitHub repo에서 SKILL.md 후보 탐색
        try:
            candidates = list_skill_md_candidates(r.repo)
        except Exception:
            candidates = []

        if not candidates:
            # SKILL.md를 못찾아도 raw로는 남긴다 (markdown_only/unsupported로)
            external_id = _stable_external_id("awesome_list", r.repo, None)
            upsert_raw_skill(
                db,
                source_id=awesome_src.id,
                external_id=external_id,
                skill_url=r.url or f"https://github.com/{r.repo}",
                name_raw=r.name,
                description_raw=r.desc,
                category_raw=None,
                tags_raw=None,
                github_repo=r.repo,
                skill_path=None,
                license_raw=None,
                data_json={"hint": "no_skill_md_found"},
                fetch_status="ok",
                source_revision=None,
                status="queued",
            )
            inserted += 1
            continue

        # candidates 중 상위 몇 개만
        for c in candidates[:5]:
            external_id = _stable_external_id("awesome_list", c.repo, c.path)
            upsert_raw_skill(
                db,
                source_id=awesome_src.id,
                external_id=external_id,
                skill_url=f"https://github.com/{c.repo}/blob/main/{c.path}",
                name_raw=r.name,
                description_raw=r.desc,
                category_raw=None,
                tags_raw=None,
                github_repo=c.repo,
                skill_path=c.path,
                license_raw=None,
                data_json={"download_url": c.download_url},
                fetch_status="ok",
                source_revision=None,
                status="queued",
            )
            inserted += 1

    db.commit()
    return {"ok": True, "raw_upserted": inserted}


def parse_queued_raw_skills(db: Session) -> dict:
    """
    raw_skills 중 queued 상태이면서 skill_path가 있는 것부터 파싱한다.
    """
    max_n = settings.PARSER_MAX_RAW_SKILLS_PER_RUN
    stmt = (
        select(RawSkill)
        .where(RawSkill.status.in_(["queued", "new"]))
        .order_by(RawSkill.updated_at.desc())
        .limit(max_n)
    )
    items = db.execute(stmt).scalars().all()

    parsed = 0
    for rs in items:
        if not rs.github_repo or not rs.skill_path:
            rs.parse_status = "markdown_only"
            rs.parse_errors = (rs.parse_errors or []) + ["no_skill_path"]
            rs.status = "queued"
            continue

        # download SKILL.md
        try:
            # data_json.download_url 우선 사용
            dl = None
            if isinstance(rs.data_json, dict):
                dl = rs.data_json.get("download_url")
            if not dl:
                # fallback: 다시 candidates 탐색
                cands = list_skill_md_candidates(rs.github_repo)
                dl = cands[0].download_url if cands else None
            if not dl:
                rs.parse_status = "unsupported"
                rs.parse_errors = (rs.parse_errors or []) + ["download_url_missing"]
                rs.status = "queued"
                continue

            text = download_file_text(dl)
        except Exception:
            rs.fetch_status = "error"
            rs.parse_status = "unsupported"
            rs.parse_errors = (rs.parse_errors or []) + ["download_failed"]
            rs.status = "queued"
            continue

        parsed_doc = parse_skill_md(text)
        caps = {}
        try:
            caps = detect_repo_capabilities(rs.github_repo)
        except Exception:
            caps = {}

        # store
        rs.parse_status = parsed_doc.parse_status
        rs.parse_errors = parsed_doc.parse_errors
        rs.data_json = {
            "download_url": dl,
            "frontmatter": parsed_doc.frontmatter,
            "normalized": parsed_doc.normalized,
            "body_md": parsed_doc.body_md,
            "capabilities": caps,
        }
        rs.status = "queued"  # 운영자 승인 큐로 대기
        parsed += 1

    db.commit()
    return {"ok": True, "parsed": parsed}


def run(db: Session) -> dict:
    r1 = ingest_raw(db)
    r2 = parse_queued_raw_skills(db)
    return {"ingest": r1, "parse": r2}

8) Admin “프리뷰 / 잠재 중복 후보” API 추가
8.1 app/api/admin_quality.py
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from rapidfuzz import fuzz

from app.api.deps import get_db
from app.security.auth import decode_token
from app.models.raw_skill import RawSkill
from app.models.skill import Skill

router = APIRouter()
bearer = HTTPBearer(auto_error=True)


def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload


@router.get("/raw-skills/{raw_skill_id}/preview")
def raw_skill_preview(raw_skill_id: uuid.UUID, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rs = db.get(RawSkill, raw_skill_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Not found")

    # data_json에 파싱 결과가 있으면 그걸 그대로 반환
    preview = {}
    if isinstance(rs.data_json, dict):
        preview = {
            "frontmatter": rs.data_json.get("frontmatter"),
            "normalized": rs.data_json.get("normalized"),
            "capabilities": rs.data_json.get("capabilities"),
            "body_md": rs.data_json.get("body_md"),
        }

    return {
        "id": str(rs.id),
        "source_id": str(rs.source_id),
        "name_raw": rs.name_raw,
        "description_raw": rs.description_raw,
        "category_raw": rs.category_raw,
        "tags_raw": rs.tags_raw,
        "skill_url": rs.skill_url,
        "github_repo": rs.github_repo,
        "skill_path": rs.skill_path,
        "parse_status": rs.parse_status,
        "parse_errors": rs.parse_errors,
        "fetch_status": rs.fetch_status,
        "status": rs.status,
        "preview": preview,
    }


@router.get("/raw-skills/{raw_skill_id}/candidates")
def raw_skill_candidates(
    raw_skill_id: uuid.UUID,
    payload: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
):
    rs = db.get(RawSkill, raw_skill_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Not found")

    target_name = (rs.name_raw or "").strip()
    target_desc = (rs.description_raw or "").strip()
    if isinstance(rs.data_json, dict):
        norm = rs.data_json.get("normalized") or {}
        if isinstance(norm, dict):
            target_name = (norm.get("name") or target_name).strip()
            target_desc = (norm.get("summary") or target_desc).strip()

    # MVP: 전수 대비(스킬 수 적을 때 충분). 커지면 trigram/fts/embedding로 교체.
    skills = db.execute(select(Skill).where(Skill.status.in_(["active", "pending", "draft"]))).scalars().all()

    scored = []
    for sk in skills:
        n = (sk.name or "").strip()
        d = (sk.summary or "").strip()
        s1 = fuzz.token_set_ratio(target_name, n) if target_name and n else 0
        s2 = fuzz.token_set_ratio(target_desc, d) if target_desc and d else 0
        score = int(0.7 * s1 + 0.3 * s2)
        if score > 40:
            scored.append((score, sk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    return {
        "raw_skill_id": str(rs.id),
        "target": {"name": target_name, "summary": target_desc[:240]},
        "candidates": [
            {
                "score": s,
                "skill_id": str(sk.id),
                "name": sk.name,
                "summary": sk.summary,
                "canonical_repo": sk.canonical_repo,
                "status": sk.status,
            }
            for s, sk in top
        ],
    }

8.2 app/api/router.py에 admin_quality 라우터 연결
from fastapi import APIRouter
from app.api import health, skills, taxonomy, rankings, events, admin
from app.api import admin_skills
from app.api import admin_quality

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(skills.router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy.router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(admin_skills.router, prefix="/admin/skills", tags=["admin-skills"])
router.include_router(admin_quality.router, prefix="/admin", tags=["admin-quality"])

9) 워커 실행 “한 방” (ingest+parse+popularity+snapshot)
9.1 app/workers/run_all.py 교체 (풀 파이프라인)
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.workers.ingest_and_parse import run as run_ingest_parse
from app.workers.compute_popularity import run as run_popularity
from app.workers.build_rank_snapshots import run as run_snapshots


def main():
    db: Session = SessionLocal()
    try:
        r0 = run_ingest_parse(db)
        r1 = run_popularity(db)
        r2 = run_snapshots(db)
        print({"ingest_parse": r0, "popularity": r1, "snapshots": r2})
    finally:
        db.close()


if __name__ == "__main__":
    main()

10) 운영 기준: “다음 단계 없이” 바로 운영하는 방법
10.1 로컬/서버에서 cron (예: 매일 04:00 KST)
0 4 * * * cd /path/to/agent-skills-marketplace && /path/to/python -m app.workers.run_all >> logs/worker.log 2>&1

11) 최종적으로 “완성된 상태” 정의 (지금 이 시점)

이제 너 프로젝트는 다음이 완성된 상태야:

외부 리스트에서 repo를 자동 수집 → raw_skills upsert

GitHub에서 SKILL.md 위치 탐색 → 다운로드 → 파싱 → data_json에 결과 저장

운영자는 admin 콘솔(엔드포인트)로

raw 프리뷰 확인 (/admin/raw-skills/{id}/preview)

잠재 중복 후보 확인 (/admin/raw-skills/{id}/candidates)

승인/병합 실행 (/admin/raw-skills/approve 기존 구현)

이벤트 집계 → popularity_score 계산

TOP10 스냅샷 생성 → UI는 rankings API로 조회 가능

바로 테스트 순서 (가장 빠른 루트)

마이그레이션

alembic upgrade head

API 실행

uvicorn app.main:app --reload

워커 실행(수동)

python -m app.workers.run_all

Admin 로그인

POST /admin/login

raw 리스트

GET /admin/raw-skills

raw 프리뷰/중복 후보

GET /admin/raw-skills/{id}/preview