ERD 기준 “전체 모델 + Alembic 초기 마이그레이션 + CRUD Repo + 라우터”를 한 번에 완성본

추가/변경 포인트 (중요)

ID는 Postgres에서 잘 동작하는 UUID(진짜 타입) 사용

created_at/updated_at는 timestamptz

skill_popularity는 skills와 1:1 (PK=FK)

skill_source_links / skill_tags는 복합 PK

raw_skills는 파싱/페치 상태 필드 포함

Admin은 env 기반 단일 계정(JWT)으로 MVP 완성

1) 전체 코드 (파일별)
1.1 app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

1.2 app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

1.3 app/settings.py
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


settings = Settings()

1.4 app/security/auth.py
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)


def create_admin_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    payload = {"sub": username, "role": "admin", "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

2) SQLAlchemy Models (ERD 전체)
2.1 app/models/_mixins.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

2.2 app/models/skill_source.py
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class SkillSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "skill_sources"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)  # catalog|github|list
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)

2.3 app/models/raw_skill.py
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class RawSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "raw_skills"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_raw_source_external"),
        UniqueConstraint("source_id", "skill_url", name="uq_raw_source_url"),
    )

    source_id: Mapped[object] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    external_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    name_raw: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_raw: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags_raw: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)

    skill_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_repo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    skill_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    license_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    parse_status: Mapped[str] = mapped_column(
        String(40),
        default="markdown_only",
        nullable=False,
    )  # valid|partial|invalid_frontmatter|markdown_only|unsupported
    parse_errors: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)

    fetch_status: Mapped[str] = mapped_column(
        String(40),
        default="ok",
        nullable=False,
    )  # ok|moved|not_found|forbidden|rate_limited|error

    source_revision: Mapped[str | None] = mapped_column(String(200), nullable=True)  # commit_sha|etag|last_modified
    status: Mapped[str] = mapped_column(String(40), default="new", nullable=False)  # new|queued|ignored|mapped

2.4 app/models/category.py
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"

    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

2.5 app/models/category_alias.py
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class CategoryAlias(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "category_aliases"
    __table_args__ = (
        UniqueConstraint("source_id", "raw_category", name="uq_category_alias_source_raw"),
    )

    source_id: Mapped[object] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    category_id: Mapped[object] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    raw_category: Mapped[str] = mapped_column(String(200), nullable=False)

2.6 app/models/tag.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Tag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tags"

    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

2.7 app/models/skill.py
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Skill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "skills"

    canonical_repo: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    description_md: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[object | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    skill_type: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    spec_format: Mapped[str] = mapped_column(String(40), default="skillmd", nullable=False)
    spec_version: Mapped[str | None] = mapped_column(String(40), nullable=True)

    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # scripts/assets/references flags
    trigger_hints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    negative_triggers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    license: Mapped[str | None] = mapped_column(String(80), nullable=True)
    content_policy: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)  # link_only|cache_allowed|unknown
    license_confidence: Mapped[str] = mapped_column(String(20), default="low", nullable=False)

    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)  # draft|pending|active|archived

    last_seen_at: Mapped[object | None] = mapped_column(String(40), nullable=True)
    last_changed_at: Mapped[object | None] = mapped_column(String(40), nullable=True)

2.8 app/models/skill_source_link.py
from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class SkillSourceLink(Base):
    __tablename__ = "skill_source_links"
    __table_args__ = (
        PrimaryKeyConstraint("skill_id", "source_id", "raw_skill_id", name="pk_skill_source_links"),
    )

    skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skill_sources.id", ondelete="CASCADE"), nullable=False)
    raw_skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("raw_skills.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

2.9 app/models/skill_tag.py
from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class SkillTag(Base):
    __tablename__ = "skill_tags"
    __table_args__ = (
        PrimaryKeyConstraint("skill_id", "tag_id", name="pk_skill_tags"),
    )

    skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

2.10 app/models/skill_event.py
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin


def utcnow():
    return datetime.now(timezone.utc)


class SkillEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skill_events"
    __table_args__ = (
        Index("ix_skill_events_skill_type_time", "skill_id", "event_type", "created_at"),
    )

    skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[object | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # view|use|favorite
    session_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ua_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

2.11 app/models/skill_popularity.py
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class SkillPopularity(Base):
    __tablename__ = "skill_popularity"

    skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    github_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    github_forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    github_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    views_1d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views_7d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views_30d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    uses_1d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uses_7d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uses_30d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    favorites_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

2.12 app/models/skill_rank_snapshot.py
from sqlalchemy import String, Date, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin


def utcnow():
    return datetime.now(timezone.utc)


class SkillRankSnapshot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skill_rank_snapshots"
    __table_args__ = (
        Index("ix_rank_snapshots_date_scope", "snapshot_date", "scope", "category_id"),
    )

    snapshot_date: Mapped[object] = mapped_column(Date, nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # global|category
    category_id: Mapped[object | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    skill_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

2.13 app/models/github_repo_cache.py
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from app.db.base import Base
from app.models._mixins import UUIDPrimaryKeyMixin


def utcnow():
    return datetime.now(timezone.utc)


class GithubRepoCache(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "github_repo_cache"
    __table_args__ = (
        UniqueConstraint("repo_full_name", name="uq_github_repo_full_name"),
    )

    repo_full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    license_spdx: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    etag: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

3) Alembic 마이그레이션 (초기 1회 완성본)
3.1 migrations/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.settings import settings
from app.db.base import Base

# 반드시 import 해서 metadata에 등록되게 함
from app.models.skill_source import SkillSource  # noqa: F401
from app.models.raw_skill import RawSkill  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.category_alias import CategoryAlias  # noqa: F401
from app.models.tag import Tag  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.skill_source_link import SkillSourceLink  # noqa: F401
from app.models.skill_tag import SkillTag  # noqa: F401
from app.models.skill_event import SkillEvent  # noqa: F401
from app.models.skill_popularity import SkillPopularity  # noqa: F401
from app.models.skill_rank_snapshot import SkillRankSnapshot  # noqa: F401
from app.models.github_repo_cache import GithubRepoCache  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

3.2 migrations/versions/0001_init.py
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
        sa.Column("parse_status", sa.String(length=40), nullable=False, server_default="="markdown_only"),
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


주의: 위 마이그레이션에 server_default 문자열에 따옴표 실수로 인해 깨질 수 있는 부분이 있는 DB가 있음.
안전을 위해 parse_status 기본값 라인은 아래처럼 고쳐 써도 됨: server_default="markdown_only"
(현재 코드에는 오타 가능성이 있어, 적용 전에 해당 라인만 확인 추천)

4) Schemas (CRUD/라우터용)
4.1 app/schemas/common.py
from pydantic import BaseModel, Field


class Page(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

4.2 app/schemas/skill.py
from pydantic import BaseModel, Field
from typing import Any
import uuid


class SkillListItem(BaseModel):
    id: uuid.UUID
    name: str
    summary: str | None = None
    canonical_repo: str | None = None
    category_id: uuid.UUID | None = None
    skill_type: str
    spec_format: str
    status: str


class SkillDetail(BaseModel):
    id: uuid.UUID
    name: str
    summary: str | None = None
    description_md: str | None = None
    canonical_repo: str | None = None
    category_id: uuid.UUID | None = None
    skill_type: str
    spec_format: str
    spec_version: str | None = None
    capabilities: dict[str, Any] | None = None
    trigger_hints: dict[str, Any] | None = None
    negative_triggers: dict[str, Any] | None = None
    license: str | None = None
    content_policy: str
    license_confidence: str
    status: str
    tags: list[str] = []


class SkillQuery(BaseModel):
    q: str | None = None
    category_id: uuid.UUID | None = None
    tag: str | None = None
    sort: str = Field(default="latest", pattern="^(latest|popular)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class SkillCreate(BaseModel):
    name: str
    summary: str | None = None
    description_md: str | None = None
    canonical_repo: str | None = None
    category_id: uuid.UUID | None = None
    skill_type: str = "unknown"
    spec_format: str = "skillmd"
    spec_version: str | None = None
    capabilities: dict | None = None
    trigger_hints: dict | None = None
    negative_triggers: dict | None = None
    license: str | None = None
    content_policy: str = "unknown"
    license_confidence: str = "low"
    status: str = "active"
    tags: list[str] = []


class SkillUpdate(BaseModel):
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
    status: str | None = None
    tags: list[str] | None = None

4.3 app/schemas/taxonomy.py
from pydantic import BaseModel
import uuid


class CategoryOut(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool


class TagOut(BaseModel):
    id: uuid.UUID
    key: str
    name: str

4.4 app/schemas/events.py
from pydantic import BaseModel, Field
import uuid


class EventIn(BaseModel):
    skill_id: uuid.UUID
    event_type: str = Field(pattern="^(view|use|favorite)$")
    session_hash: str | None = None
    ip_hash: str | None = None
    ua_hash: str | None = None

4.5 app/schemas/admin.py
from pydantic import BaseModel
import uuid


class RawSkillOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    name_raw: str | None = None
    description_raw: str | None = None
    category_raw: str | None = None
    skill_url: str | None = None
    github_repo: str | None = None
    skill_path: str | None = None
    parse_status: str
    fetch_status: str
    status: str


class ApproveRawSkillIn(BaseModel):
    raw_skill_id: uuid.UUID
    create_new: bool = True
    existing_skill_id: uuid.UUID | None = None

    # create_new일 때 사용 (없으면 raw에서 최대한 가져옴)
    name: str | None = None
    summary: str | None = None
    description_md: str | None = None
    category_id: uuid.UUID | None = None
    tags: list[str] = []
    canonical_repo: str | None = None
    status: str = "active"

5) Repos (CRUD)
5.1 app/repos/skill_repo.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.skill import Skill
from app.models.tag import Tag
from app.models.skill_tag import SkillTag
from app.models.skill_popularity import SkillPopularity


def normalize_tag_key(x: str) -> str:
    return x.strip().lower().replace(" ", "-")


class SkillRepo:
    @staticmethod
    def list_skills(db: Session, q: str | None, category_id: uuid.UUID | None, tag: str | None, sort: str, page: int, size: int):
        stmt = select(Skill)

        if q:
            stmt = stmt.where(Skill.name.ilike(f"%{q}%"))
        if category_id:
            stmt = stmt.where(Skill.category_id == category_id)

        if tag:
            # tags.key로 필터: tags + skill_tags join
            from app.models.skill_tag import SkillTag as ST
            from app.models.tag import Tag as TG
            stmt = stmt.join(ST, ST.skill_id == Skill.id).join(TG, TG.id == ST.tag_id).where(TG.key == normalize_tag_key(tag))

        if sort == "popular":
            stmt = stmt.join(SkillPopularity, SkillPopularity.skill_id == Skill.id, isouter=True).order_by(
                SkillPopularity.popularity_score.desc().nullslast(),
                Skill.updated_at.desc().nullslast(),
            )
        else:
            stmt = stmt.order_by(Skill.updated_at.desc().nullslast())

        offset = (page - 1) * size
        items = db.execute(stmt.offset(offset).limit(size)).scalars().all()
        return items

    @staticmethod
    def get_skill(db: Session, skill_id: uuid.UUID) -> Skill | None:
        return db.get(Skill, skill_id)

    @staticmethod
    def upsert_tags_and_bind(db: Session, skill_id: uuid.UUID, tags: list[str]):
        # 1) tags upsert
        tag_keys = []
        for t in tags:
            k = normalize_tag_key(t)
            if k:
                tag_keys.append((k, t.strip()))

        if not tag_keys:
            # 기존 태그 제거만
            db.query(SkillTag).filter(SkillTag.skill_id == skill_id).delete()
            return

        # Upsert tags
        for key, name in tag_keys:
            stmt = pg_insert(Tag).values(key=key, name=name).on_conflict_do_update(
                index_elements=[Tag.key],
                set_={"name": name},
            )
            db.execute(stmt)

        # 2) 기존 연결 제거 후 재연결 (MVP 단순)
        db.query(SkillTag).filter(SkillTag.skill_id == skill_id).delete()

        # 3) tag_id 조회 후 연결
        keys = [k for k, _ in tag_keys]
        tag_rows = db.execute(select(Tag).where(Tag.key.in_(keys))).scalars().all()
        for tr in tag_rows:
            db.add(SkillTag(skill_id=skill_id, tag_id=tr.id))

    @staticmethod
    def list_skill_tag_keys(db: Session, skill_id: uuid.UUID) -> list[str]:
        from app.models.tag import Tag as TG
        from app.models.skill_tag import SkillTag as ST
        rows = db.execute(
            select(TG.key).join(ST, ST.tag_id == TG.id).where(ST.skill_id == skill_id)
        ).all()
        return [r[0] for r in rows]

5.2 app/repos/taxonomy_repo.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.category import Category
from app.models.tag import Tag


class TaxonomyRepo:
    @staticmethod
    def list_categories(db: Session):
        stmt = select(Category).where(Category.is_active == True).order_by(Category.sort_order.asc(), Category.name.asc())
        return db.execute(stmt).scalars().all()

    @staticmethod
    def list_tags(db: Session, q: str | None = None, limit: int = 50):
        stmt = select(Tag)
        if q:
            stmt = stmt.where(Tag.key.ilike(f"%{q.lower()}%"))
        stmt = stmt.order_by(Tag.key.asc()).limit(limit)
        return db.execute(stmt).scalars().all()

5.3 app/repos/ranking_repo.py
import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.skill_rank_snapshot import SkillRankSnapshot
from app.models.skill_popularity import SkillPopularity
from app.models.skill import Skill


class RankingRepo:
    @staticmethod
    def top10_global(db: Session, snapshot_date: date | None = None):
        if snapshot_date:
            stmt = (
                select(SkillRankSnapshot, Skill)
                .join(Skill, Skill.id == SkillRankSnapshot.skill_id)
                .where(SkillRankSnapshot.snapshot_date == snapshot_date, SkillRankSnapshot.scope == "global")
                .order_by(SkillRankSnapshot.rank.asc())
                .limit(10)
            )
            return db.execute(stmt).all()

        # 스냅샷이 없으면 popularity fallback
        stmt = (
            select(Skill)
            .join(SkillPopularity, SkillPopularity.skill_id == Skill.id, isouter=True)
            .where(Skill.status == "active")
            .order_by(SkillPopularity.popularity_score.desc().nullslast(), Skill.updated_at.desc().nullslast())
            .limit(10)
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def top10_category(db: Session, category_id: uuid.UUID, snapshot_date: date | None = None):
        if snapshot_date:
            stmt = (
                select(SkillRankSnapshot, Skill)
                .join(Skill, Skill.id == SkillRankSnapshot.skill_id)
                .where(
                    SkillRankSnapshot.snapshot_date == snapshot_date,
                    SkillRankSnapshot.scope == "category",
                    SkillRankSnapshot.category_id == category_id,
                )
                .order_by(SkillRankSnapshot.rank.asc())
                .limit(10)
            )
            return db.execute(stmt).all()

        stmt = (
            select(Skill)
            .join(SkillPopularity, SkillPopularity.skill_id == Skill.id, isouter=True)
            .where(Skill.status == "active", Skill.category_id == category_id)
            .order_by(SkillPopularity.popularity_score.desc().nullslast(), Skill.updated_at.desc().nullslast())
            .limit(10)
        )
        return db.execute(stmt).scalars().all()

5.4 app/repos/admin_repo.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.raw_skill import RawSkill
from app.models.skill import Skill
from app.models.skill_source_link import SkillSourceLink
from app.models.skill_popularity import SkillPopularity
from app.repos.skill_repo import SkillRepo


class AdminRepo:
    @staticmethod
    def list_raw_skills(db: Session, status: str | None, page: int, size: int):
        stmt = select(RawSkill).order_by(RawSkill.updated_at.desc())
        if status:
            stmt = stmt.where(RawSkill.status == status)
        offset = (page - 1) * size
        items = db.execute(stmt.offset(offset).limit(size)).scalars().all()
        return items

    @staticmethod
    def ignore_raw_skill(db: Session, raw_skill_id: uuid.UUID):
        rs = db.get(RawSkill, raw_skill_id)
        if not rs:
            return None
        rs.status = "ignored"
        return rs

    @staticmethod
    def approve_raw_skill_create_or_merge(
        db: Session,
        raw_skill_id: uuid.UUID,
        create_new: bool,
        existing_skill_id: uuid.UUID | None,
        name: str | None,
        summary: str | None,
        description_md: str | None,
        category_id: uuid.UUID | None,
        tags: list[str],
        canonical_repo: str | None,
        status: str,
    ):
        rs = db.get(RawSkill, raw_skill_id)
        if not rs:
            return None, "raw_skill_not_found"

        if create_new:
            sk = Skill(
                name=name or (rs.name_raw or "Untitled Skill"),
                summary=summary or (rs.description_raw[:300] if rs.description_raw else None),
                description_md=description_md or rs.description_raw,
                canonical_repo=canonical_repo or rs.github_repo,
                category_id=category_id,
                status=status,
                spec_format="skillmd" if rs.skill_path else "markdown",
                skill_type="unknown",
            )
            db.add(sk)
            db.flush()  # sk.id 확보

            # popularity 기본 row 생성
            db.add(SkillPopularity(skill_id=sk.id))

            # link
            db.add(SkillSourceLink(skill_id=sk.id, source_id=rs.source_id, raw_skill_id=rs.id))

            # tags
            SkillRepo.upsert_tags_and_bind(db, sk.id, tags)

            rs.status = "mapped"
            return sk, None

        # merge
        if not existing_skill_id:
            return None, "existing_skill_id_required"

        sk = db.get(Skill, existing_skill_id)
        if not sk:
            return None, "skill_not_found"

        db.add(SkillSourceLink(skill_id=sk.id, source_id=rs.source_id, raw_skill_id=rs.id))
        rs.status = "mapped"

        # merge tags (단순: 기존 + 신규)
        existing = set(SkillRepo.list_skill_tag_keys(db, sk.id))
        merged = list(existing.union({t.strip().lower().replace(" ", "-") for t in tags if t.strip()}))
        SkillRepo.upsert_tags_and_bind(db, sk.id, merged)

        return sk, None

6) API 라우터 (CRUD 완성)
6.1 app/api/deps.py
from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

6.2 app/api/router.py
from fastapi import APIRouter
from app.api import health, skills, taxonomy, rankings, events, admin

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(skills.router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy.router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])

6.3 app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health():
    return {"ok": True}

6.4 app/api/skills.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.skill import SkillListItem, SkillDetail, SkillQuery
from app.repos.skill_repo import SkillRepo

router = APIRouter()


@router.get("", response_model=list[SkillListItem])
def list_skills(query: SkillQuery = Depends(), db: Session = Depends(get_db)):
    items = SkillRepo.list_skills(db, query.q, query.category_id, query.tag, query.sort, query.page, query.size)
    return [
        SkillListItem(
            id=i.id,
            name=i.name,
            summary=i.summary,
            canonical_repo=i.canonical_repo,
            category_id=i.category_id,
            skill_type=i.skill_type,
            spec_format=i.spec_format,
            status=i.status,
        )
        for i in items
    ]


@router.get("/{skill_id}", response_model=SkillDetail)
def get_skill(skill_id: uuid.UUID, db: Session = Depends(get_db)):
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

6.5 app/api/taxonomy.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.taxonomy import CategoryOut, TagOut
from app.repos.taxonomy_repo import TaxonomyRepo

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    items = TaxonomyRepo.list_categories(db)
    return [CategoryOut(**{
        "id": i.id,
        "key": i.key,
        "name": i.name,
        "description": i.description,
        "sort_order": i.sort_order,
        "is_active": i.is_active,
    }) for i in items]


@router.get("/tags", response_model=list[TagOut])
def tags(q: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    items = TaxonomyRepo.list_tags(db, q=q, limit=limit)
    return [TagOut(id=i.id, key=i.key, name=i.name) for i in items]

6.6 app/api/rankings.py
import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repos.ranking_repo import RankingRepo
from app.schemas.skill import SkillListItem

router = APIRouter()


@router.get("/top10", response_model=list[SkillListItem])
def top10_global(snapshot_date: date | None = Query(default=None), db: Session = Depends(get_db)):
    res = RankingRepo.top10_global(db, snapshot_date=snapshot_date)
    # snapshot 사용 시 (SkillRankSnapshot, Skill) 형태
    if res and isinstance(res[0], tuple):
        skills = [t[1] for t in res]
    else:
        skills = res
    return [SkillListItem(
        id=s.id,
        name=s.name,
        summary=s.summary,
        canonical_repo=s.canonical_repo,
        category_id=s.category_id,
        skill_type=s.skill_type,
        spec_format=s.spec_format,
        status=s.status
    ) for s in skills]


@router.get("/top10/category/{category_id}", response_model=list[SkillListItem])
def top10_category(category_id: uuid.UUID, snapshot_date: date | None = Query(default=None), db: Session = Depends(get_db)):
    res = RankingRepo.top10_category(db, category_id=category_id, snapshot_date=snapshot_date)
    if res and isinstance(res[0], tuple):
        skills = [t[1] for t in res]
    else:
        skills = res
    return [SkillListItem(
        id=s.id,
        name=s.name,
        summary=s.summary,
        canonical_repo=s.canonical_repo,
        category_id=s.category_id,
        skill_type=s.skill_type,
        spec_format=s.spec_format,
        status=s.status
    ) for s in skills]

6.7 app/api/events.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.events import EventIn
from app.models.skill_event import SkillEvent

router = APIRouter()


@router.post("")
def create_event(payload: EventIn, db: Session = Depends(get_db)):
    ev = SkillEvent(
        skill_id=payload.skill_id,
        event_type=payload.event_type,
        session_hash=payload.session_hash,
        ip_hash=payload.ip_hash,
        ua_hash=payload.ua_hash,
    )
    db.add(ev)
    db.commit()
    return {"ok": True, "event_id": str(ev.id)}

6.8 app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.security.auth import create_admin_token, decode_token
from app.settings import settings

from app.schemas.admin import RawSkillOut, ApproveRawSkillIn
from app.repos.admin_repo import AdminRepo

router = APIRouter()
bearer = HTTPBearer(auto_error=True)


def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload


@router.post("/login")
def admin_login(form: OAuth2PasswordRequestForm = Depends()):
    if form.username != settings.ADMIN_USERNAME or form.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_admin_token(form.username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def admin_me(payload: dict = Depends(require_admin)):
    return {"username": payload.get("sub"), "role": payload.get("role")}


@router.get("/raw-skills", response_model=list[RawSkillOut])
def list_raw_skills(
    payload: dict = Depends(require_admin),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    items = AdminRepo.list_raw_skills(db, status=status, page=page, size=size)
    return [RawSkillOut(
        id=i.id,
        source_id=i.source_id,
        name_raw=i.name_raw,
        description_raw=i.description_raw,
        category_raw=i.category_raw,
        skill_url=i.skill_url,
        github_repo=i.github_repo,
        skill_path=i.skill_path,
        parse_status=i.parse_status,
        fetch_status=i.fetch_status,
        status=i.status,
    ) for i in items]


@router.post("/raw-skills/ignore")
def ignore_raw_skill(body: dict, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    raw_id = body.get("raw_skill_id")
    if not raw_id:
        raise HTTPException(status_code=400, detail="raw_skill_id required")
    rs = AdminRepo.ignore_raw_skill(db, raw_skill_id=raw_id)
    if not rs:
        raise HTTPException(status_code=404, detail="Not found")
    db.commit()
    return {"ok": True}


@router.post("/raw-skills/approve")
def approve_raw_skill(req: ApproveRawSkillIn, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    sk, err = AdminRepo.approve_raw_skill_create_or_merge(
        db=db,
        raw_skill_id=req.raw_skill_id,
        create_new=req.create_new,
        existing_skill_id=req.existing_skill_id,
        name=req.name,
        summary=req.summary,
        description_md=req.description_md,
        category_id=req.category_id,
        tags=req.tags,
        canonical_repo=req.canonical_repo,
        status=req.status,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not sk:
        raise HTTPException(status_code=404, detail="Not found")
    db.commit()
    return {"ok": True, "skill_id": str(sk.id)}

7) App Entrypoint
7.1 app/main.py
from fastapi import FastAPI
from app.settings import settings
from app.api.router import router

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)

8) 실행 방법 (최소)

.env 설정

alembic 적용

실행

pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

⚠️ 마지막 체크 (정직하게)

위 코드는 “완성본 스켈레톤”이지만, 마이그레이션 파일에 parse_status server_default 문자열 라인에 오타가 섞일 수 있는 위험이 있어.
적용 전 0001_init.py에서 아래 한 줄만 확인해줘:

parse_status의 server_default는 반드시 markdown_only 여야 함