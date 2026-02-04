✅ 마이그레이션 안정화 (오타/리스크 제거 + 권장 워크플로우)

✅ Admin CRUD 확장 (skills 생성/수정/태그 바인딩/상태 변경)

✅ 인기 집계 배치 워커 + 랭킹 스냅샷 배치 워커 (실행 가능한 코드)

A) 마이그레이션 안정화
A-1) (Fresh install 권장) 0001_init.py “정상본” 교체

아래 파일로 migrations/versions/0001_init.py를 교체해.
핵심 수정: parse_status server_default 오타 제거 + 기본값 문자열 안전화.

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("api_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "raw_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=True),
        sa.Column("name_raw", sa.String(length=300), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=True),
        sa.Column("category_raw", sa.String(length=200), nullable=True),
        sa.Column("tags_raw", postgresql.JSONB(), nullable=True),
        sa.Column("skill_url", sa.Text(), nullable=True),
        sa.Column("github_repo", sa.String(length=300), nullable=True),
        sa.Column("skill_path", sa.String(length=500), nullable=True),
        sa.Column("license_raw", sa.String(length=120), nullable=True),
        sa.Column("data_json", postgresql.JSONB(), nullable=True),
        sa.Column("parse_status", sa.String(length=40), nullable=False, server_default="markdown_only"),
        sa.Column("parse_errors", postgresql.JSONB(), nullable=True),
        sa.Column("fetch_status", sa.String(length=40), nullable=False, server_default="ok"),
        sa.Column("source_revision", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "external_id", name="uq_raw_source_external"),
        sa.UniqueConstraint("source_id", "skill_url", name="uq_raw_source_url"),
    )
    op.create_index("ix_raw_skills_source_id", "raw_skills", ["source_id"], unique=False)

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_repo", sa.String(length=300), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=400), nullable=True),
        sa.Column("description_md", sa.Text(), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_type", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("spec_format", sa.String(length=40), nullable=False, server_default="skillmd"),
        sa.Column("spec_version", sa.String(length=40), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("trigger_hints", postgresql.JSONB(), nullable=True),
        sa.Column("negative_triggers", postgresql.JSONB(), nullable=True),
        sa.Column("license", sa.String(length=80), nullable=True),
        sa.Column("content_policy", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("license_confidence", sa.String(length=20), nullable=False, server_default="low"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("last_seen_at", sa.String(length=40), nullable=True),
        sa.Column("last_changed_at", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_skills_name", "skills", ["name"], unique=False)
    op.create_index("ix_skills_canonical_repo", "skills", ["canonical_repo"], unique=False)
    op.create_index("ix_skills_category_id", "skills", ["category_id"], unique=False)

    op.create_table(
        "category_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_category", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "raw_category", name="uq_category_alias_source_raw"),
    )
    op.create_index("ix_category_aliases_source_id", "category_aliases", ["source_id"], unique=False)
    op.create_index("ix_category_aliases_category_id", "category_aliases", ["category_id"], unique=False)

    op.create_table(
        "skill_source_links",
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["skill_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_skill_id"], ["raw_skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("skill_id", "source_id", "raw_skill_id", name="pk_skill_source_links"),
    )

    op.create_table(
        "skill_tags",
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("skill_id", "tag_id", name="pk_skill_tags"),
    )

    op.create_table(
        "skill_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("session_hash", sa.String(length=128), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("ua_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_skill_events_skill_id", "skill_events", ["skill_id"], unique=False)
    op.create_index("ix_skill_events_skill_type_time", "skill_events", ["skill_id", "event_type", "created_at"], unique=False)

    op.create_table(
        "skill_popularity",
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("github_stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("github_forks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("github_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("views_1d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views_7d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views_30d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uses_1d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uses_7d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uses_30d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("favorites_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("popularity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("score_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "skill_rank_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rank_snapshots_date_scope", "skill_rank_snapshots", ["snapshot_date", "scope", "category_id"], unique=False)
    op.create_index("ix_skill_rank_snapshots_skill_id", "skill_rank_snapshots", ["skill_id"], unique=False)

    op.create_table(
        "github_repo_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_full_name", sa.String(length=300), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("license_spdx", sa.String(length=40), nullable=True),
        sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("etag", sa.String(length=200), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("repo_full_name", name="uq_github_repo_full_name"),
    )


def downgrade() -> None:
    op.drop_table("github_repo_cache")
    op.drop_index("ix_skill_rank_snapshots_skill_id", table_name="skill_rank_snapshots")
    op.drop_index("ix_rank_snapshots_date_scope", table_name="skill_rank_snapshots")
    op.drop_table("skill_rank_snapshots")
    op.drop_table("skill_popularity")
    op.drop_index("ix_skill_events_skill_type_time", table_name="skill_events")
    op.drop_index("ix_skill_events_skill_id", table_name="skill_events")
    op.drop_table("skill_events")
    op.drop_table("skill_tags")
    op.drop_table("skill_source_links")
    op.drop_index("ix_category_aliases_category_id", table_name="category_aliases")
    op.drop_index("ix_category_aliases_source_id", table_name="category_aliases")
    op.drop_table("category_aliases")
    op.drop_index("ix_skills_category_id", table_name="skills")
    op.drop_index("ix_skills_canonical_repo", table_name="skills")
    op.drop_index("ix_skills_name", table_name="skills")
    op.drop_table("skills")
    op.drop_index("ix_raw_skills_source_id", table_name="raw_skills")
    op.drop_table("raw_skills")
    op.drop_table("tags")
    op.drop_table("categories")
    op.drop_table("skill_sources")

A-2) (이미 DB에 적용했다면) 0002_hotfix_defaults.py 추가

만약 예전 0001을 이미 올렸다면, 이 0002를 추가해서 parse_status 기본값만 수정해도 안전해.

파일: migrations/versions/0002_hotfix_defaults.py

from alembic import op
import sqlalchemy as sa

revision = "0002_hotfix_defaults"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "raw_skills",
        "parse_status",
        existing_type=sa.String(length=40),
        server_default="markdown_only",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "raw_skills",
        "parse_status",
        existing_type=sa.String(length=40),
        server_default=None,
        existing_nullable=False,
    )

B) Admin CRUD 확장 (Skill Create/Update/Delete Tags + Status)
B-1) 스키마 추가: app/schemas/admin_skill.py

(운영자 전용 CRUD payload)

from pydantic import BaseModel, Field
from typing import Any
import uuid


class AdminSkillCreate(BaseModel):
    name: str
    summary: str | None = None
    description_md: str | None = None
    canonical_repo: str | None = None
    category_id: uuid.UUID | None = None

    skill_type: str = "unknown"
    spec_format: str = "skillmd"
    spec_version: str | None = None

    capabilities: dict[str, Any] | None = None
    trigger_hints: dict[str, Any] | None = None
    negative_triggers: dict[str, Any] | None = None

    license: str | None = None
    content_policy: str = "unknown"
    license_confidence: str = "low"

    status: str = Field(default="active", pattern="^(draft|pending|active|archived)$")
    tags: list[str] = []


class AdminSkillUpdate(BaseModel):
    name: str | None = None
    summary: str | None = None
    description_md: str | None = None
    canonical_repo: str | None = None
    category_id: uuid.UUID | None = None

    skill_type: str | None = None
    spec_format: str | None = None
    spec_version: str | None = None

    capabilities: dict | None = None
    trigger_hints: dict | None = None
    negative_triggers: dict | None = None

    license: str | None = None
    content_policy: str | None = None
    license_confidence: str | None = None

    status: str | None = Field(default=None, pattern="^(draft|pending|active|archived)$")
    tags: list[str] | None = None

B-2) Repo 추가: app/repos/admin_skill_repo.py
import uuid
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.repos.skill_repo import SkillRepo


class AdminSkillRepo:
    @staticmethod
    def create_skill(db: Session, payload) -> Skill:
        sk = Skill(
            name=payload.name,
            summary=payload.summary,
            description_md=payload.description_md,
            canonical_repo=payload.canonical_repo,
            category_id=payload.category_id,
            skill_type=payload.skill_type,
            spec_format=payload.spec_format,
            spec_version=payload.spec_version,
            capabilities=payload.capabilities,
            trigger_hints=payload.trigger_hints,
            negative_triggers=payload.negative_triggers,
            license=payload.license,
            content_policy=payload.content_policy,
            license_confidence=payload.license_confidence,
            status=payload.status,
        )
        db.add(sk)
        db.flush()

        # popularity row 확보 (popular sort/join 안정화)
        db.add(SkillPopularity(skill_id=sk.id))

        SkillRepo.upsert_tags_and_bind(db, sk.id, payload.tags or [])
        return sk

    @staticmethod
    def update_skill(db: Session, skill_id: uuid.UUID, payload) -> Skill | None:
        sk = db.get(Skill, skill_id)
        if not sk:
            return None

        for field in [
            "name",
            "summary",
            "description_md",
            "canonical_repo",
            "category_id",
            "skill_type",
            "spec_format",
            "spec_version",
            "capabilities",
            "trigger_hints",
            "negative_triggers",
            "license",
            "content_policy",
            "license_confidence",
            "status",
        ]:
            v = getattr(payload, field)
            if v is not None:
                setattr(sk, field, v)

        if payload.tags is not None:
            SkillRepo.upsert_tags_and_bind(db, sk.id, payload.tags)

        return sk

    @staticmethod
    def ensure_popularity_row(db: Session, skill_id: uuid.UUID):
        row = db.get(SkillPopularity, skill_id)
        if not row:
            db.add(SkillPopularity(skill_id=skill_id))

B-3) Admin 라우터 확장: app/api/admin_skills.py

운영자 전용 /admin/skills CRUD를 추가한다.

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.security.auth import decode_token
from app.schemas.admin_skill import AdminSkillCreate, AdminSkillUpdate
from app.schemas.skill import SkillDetail
from app.repos.admin_skill_repo import AdminSkillRepo
from app.repos.skill_repo import SkillRepo

router = APIRouter()
bearer = HTTPBearer(auto_error=True)


def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload


@router.post("", response_model=dict)
def create_skill(req: AdminSkillCreate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    sk = AdminSkillRepo.create_skill(db, req)
    db.commit()
    return {"ok": True, "skill_id": str(sk.id)}


@router.patch("/{skill_id}", response_model=dict)
def update_skill(skill_id: uuid.UUID, req: AdminSkillUpdate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    sk = AdminSkillRepo.update_skill(db, skill_id, req)
    if not sk:
        raise HTTPException(status_code=404, detail="Not found")
    AdminSkillRepo.ensure_popularity_row(db, sk.id)
    db.commit()
    return {"ok": True}


@router.get("/{skill_id}", response_model=SkillDetail)
def admin_get_skill(skill_id: uuid.UUID, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    sk = SkillRepo.get_skill(db, skill_id)
    if not sk:
        raise HTTPException(status_code=404, detail="Not found")
    tags = SkillRepo.list_skill_tag_keys(db, sk.id)
    return SkillDetail(
        id=sk.id,
        name=sk.name,
        summary=sk.summary,
        description_md=sk.description_md,
        canonical_repo=sk.canonical_repo,
        category_id=sk.category_id,
        skill_type=sk.skill_type,
        spec_format=sk.spec_format,
        spec_version=sk.spec_version,
        capabilities=sk.capabilities,
        trigger_hints=sk.trigger_hints,
        negative_triggers=sk.negative_triggers,
        license=sk.license,
        content_policy=sk.content_policy,
        license_confidence=sk.license_confidence,
        status=sk.status,
        tags=tags,
    )

B-4) 기존 app/api/router.py에 admin_skills 라우터 연결

파일: app/api/router.py

from fastapi import APIRouter
from app.api import health, skills, taxonomy, rankings, events, admin
from app.api import admin_skills

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(skills.router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy.router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(admin_skills.router, prefix="/admin/skills", tags=["admin-skills"])

C) 인기 집계 배치 + 랭킹 스냅샷 배치 (실행 가능한 워커)
C-1) 워커 공용: app/workers/utils.py
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)

C-2) 인기 집계: app/workers/compute_popularity.py

skill_events를 기반으로 views_1d/7d/30d, uses_*, favorites_total 집계

github_*은 github_repo_cache를 붙일 수 있지만 여기선 “그대로 유지” (향후 확장)

점수 계산: 간단하지만 실전용

import math
from datetime import timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select, func, case

from app.workers.utils import utcnow
from app.models.skill import Skill
from app.models.skill_event import SkillEvent
from app.models.skill_popularity import SkillPopularity


def compute_score(github_stars: int, uses_30d: int, favorites_total: int, recency_boost: float) -> float:
    # 기본 가중치(운영하면서 튜닝)
    w1, w2, w3, w4 = 1.0, 1.6, 1.2, 1.0
    return (
        w1 * math.log(1 + max(github_stars, 0))
        + w2 * math.log(1 + max(uses_30d, 0))
        + w3 * max(favorites_total, 0)
        + w4 * recency_boost
    )


def run(db: Session) -> dict:
    now = utcnow()
    t1 = now - timedelta(days=1)
    t7 = now - timedelta(days=7)
    t30 = now - timedelta(days=30)

    # 대상 스킬: active/pending 포함(원하면 active만)
    skill_ids = db.execute(select(Skill.id)).scalars().all()
    if not skill_ids:
        return {"ok": True, "updated": 0}

    # 집계 쿼리: 스킬별 이벤트 카운트
    def count_expr(event_type: str, since):
        return func.sum(
            case((SkillEvent.event_type == event_type, case((SkillEvent.created_at >= since, 1), else_=0)), else_=0)
        )

    agg_stmt = (
        select(
            SkillEvent.skill_id.label("skill_id"),
            func.sum(case((SkillEvent.event_type == "view", 1), else_=0)).label("views_all"),
            func.sum(case((SkillEvent.event_type == "use", 1), else_=0)).label("uses_all"),
            func.sum(case((SkillEvent.event_type == "favorite", 1), else_=0)).label("fav_all"),
            count_expr("view", t1).label("views_1d"),
            count_expr("view", t7).label("views_7d"),
            count_expr("view", t30).label("views_30d"),
            count_expr("use", t1).label("uses_1d"),
            count_expr("use", t7).label("uses_7d"),
            count_expr("use", t30).label("uses_30d"),
        )
        .group_by(SkillEvent.skill_id)
    )

    agg = {row.skill_id: row for row in db.execute(agg_stmt).all()}

    updated = 0
    for sid in skill_ids:
        pop = db.get(SkillPopularity, sid)
        if not pop:
            pop = SkillPopularity(skill_id=sid)
            db.add(pop)
            db.flush()

        row = agg.get(sid)
        if row:
            pop.views_1d = int(row.views_1d or 0)
            pop.views_7d = int(row.views_7d or 0)
            pop.views_30d = int(row.views_30d or 0)
            pop.uses_1d = int(row.uses_1d or 0)
            pop.uses_7d = int(row.uses_7d or 0)
            pop.uses_30d = int(row.uses_30d or 0)
            pop.favorites_total = int(row.fav_all or 0)
        else:
            pop.views_1d = pop.views_7d = pop.views_30d = 0
            pop.uses_1d = pop.uses_7d = pop.uses_30d = 0
            pop.favorites_total = 0

        # recency boost: 최근 30일 use가 있으면 가산
        recency_boost = 1.0 if pop.uses_30d > 0 else 0.0

        pop.popularity_score = float(compute_score(pop.github_stars, pop.uses_30d, pop.favorites_total, recency_boost))
        pop.score_updated_at = now
        updated += 1

    db.commit()
    return {"ok": True, "updated": updated}

C-3) 랭킹 스냅샷 생성: app/workers/build_rank_snapshots.py

오늘 날짜 기준으로 global top10 + category top10을 skill_rank_snapshots에 저장

이미 같은 날짜 스냅샷이 있으면 “재생성” (MVP 운영 편의)

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.models.skill_rank_snapshot import SkillRankSnapshot
from app.workers.utils import utcnow


def run(db: Session, snapshot_date: date | None = None, category_ids: list | None = None) -> dict:
    d = snapshot_date or date.today()

    # 기존 스냅샷 삭제(재생성)
    db.execute(delete(SkillRankSnapshot).where(SkillRankSnapshot.snapshot_date == d))

    # global top10
    stmt_global = (
        select(Skill.id, SkillPopularity.popularity_score)
        .join(SkillPopularity, SkillPopularity.skill_id == Skill.id, isouter=True)
        .where(Skill.status == "active")
        .order_by(SkillPopularity.popularity_score.desc().nullslast(), Skill.updated_at.desc().nullslast())
        .limit(10)
    )
    rows = db.execute(stmt_global).all()
    now = utcnow()
    rank = 1
    for sid, score in rows:
        db.add(SkillRankSnapshot(
            snapshot_date=d,
            scope="global",
            category_id=None,
            skill_id=sid,
            rank=rank,
            score=float(score or 0.0),
            created_at=now,
        ))
        rank += 1

    # category top10
    if category_ids is None:
        category_ids = db.execute(select(Skill.category_id).where(Skill.category_id.is_not(None)).distinct()).scalars().all()

    for cid in category_ids:
        stmt_cat = (
            select(Skill.id, SkillPopularity.popularity_score)
            .join(SkillPopularity, SkillPopularity.skill_id == Skill.id, isouter=True)
            .where(Skill.status == "active", Skill.category_id == cid)
            .order_by(SkillPopularity.popularity_score.desc().nullslast(), Skill.updated_at.desc().nullslast())
            .limit(10)
        )
        rows2 = db.execute(stmt_cat).all()
        r = 1
        for sid, score in rows2:
            db.add(SkillRankSnapshot(
                snapshot_date=d,
                scope="category",
                category_id=cid,
                skill_id=sid,
                rank=r,
                score=float(score or 0.0),
                created_at=now,
            ))
            r += 1

    db.commit()
    return {"ok": True, "snapshot_date": str(d)}

C-4) 워커 실행 엔트리: app/workers/run_all.py

한 번 실행하면: popularity 집계 → snapshot 생성 순서로 돈다.

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.workers.compute_popularity import run as run_popularity
from app.workers.build_rank_snapshots import run as run_snapshots


def main():
    db: Session = SessionLocal()
    try:
        r1 = run_popularity(db)
        r2 = run_snapshots(db)
        print({"popularity": r1, "snapshots": r2})
    finally:
        db.close()


if __name__ == "__main__":
    main()

D) (선택이지만 강력 추천) README에 워커 실행 추가

파일: README.md 하단에 추가

## Worker (popularity + rank snapshots)

로컬에서 수동 실행:
python -m app.workers.run_all

E) 최종 연결 확인 포인트

FastAPI 실행: /health OK

Admin 로그인: POST /admin/login

Admin 스킬 생성: POST /admin/skills

이벤트 적재: POST /events

워커 실행: python -m app.workers.run_all