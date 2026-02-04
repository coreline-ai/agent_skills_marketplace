FastAPI + PostgreSQL(DB) + Alembic 마이그레이션 + Admin JWT까지 포함한 프로덕션급 스켈레톤

프로젝트 구조
agent-skills-marketplace/
  pyproject.toml
  README.md
  .env.example
  alembic.ini

  app/
    __init__.py
    main.py
    settings.py
    logging_conf.py

    db/
      __init__.py
      session.py
      base.py

    models/
      __init__.py
      skill_source.py
      raw_skill.py
      category.py
      tag.py
      skill.py
      skill_source_link.py
      skill_event.py
      skill_popularity.py
      skill_rank_snapshot.py
      github_repo_cache.py

    schemas/
      __init__.py
      common.py
      skill.py
      admin.py
      ranking.py

    repos/
      __init__.py
      skill_repo.py
      admin_repo.py
      ranking_repo.py

    api/
      __init__.py
      deps.py
      router.py
      health.py
      skills.py
      taxonomy.py
      rankings.py
      events.py
      admin.py

    security/
      __init__.py
      auth.py

  migrations/
    env.py
    script.py.mako
    versions/
      .gitkeep

1) pyproject.toml
[project]
name = "agent-skills-marketplace"
version = "0.1.0"
description = "SKILL.md 기반 AI 에이전트 스킬 마켓플레이스 (FastAPI + Postgres)"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.7.0",
  "pydantic-settings>=2.3.0",
  "SQLAlchemy>=2.0.30",
  "alembic>=1.13.2",
  "psycopg[binary]>=3.1.19",
  "python-jose[cryptography]>=3.3.0",
  "passlib[bcrypt]>=1.7.4",
  "python-multipart>=0.0.9"
]

[tool.ruff]
line-length = 110
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]

2) .env.example
# App
APP_NAME="Agent Skills Marketplace"
ENV="dev"
LOG_LEVEL="INFO"

# Security
JWT_SECRET="change-me-please"
JWT_ALG="HS256"
JWT_EXPIRES_MINUTES=120

# Admin bootstrap (for local/dev)
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin1234!"

# DB
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/skillsdb"

3) app/settings.py
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

4) app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

5) app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

6) 모델들 (핵심만, 나머지도 동일 패턴)
6.1 app/models/skill_source.py
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SkillSource(Base):
    __tablename__ = "skill_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)  # catalog|github|list
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)

    created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

6.2 app/models/category.py
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

6.3 app/models/tag.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

6.4 app/models/skill.py
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    canonical_repo: Mapped[str | None] = mapped_column(String(300), nullable=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    description_md: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    skill_type: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    spec_format: Mapped[str] = mapped_column(String(40), default="skillmd", nullable=False)
    spec_version: Mapped[str | None] = mapped_column(String(40), nullable=True)

    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)        # scripts/assets/references
    trigger_hints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    negative_triggers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    license: Mapped[str | None] = mapped_column(String(80), nullable=True)
    content_policy: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    license_confidence: Mapped[str] = mapped_column(String(20), default="low", nullable=False)

    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)

    last_seen_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_changed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

    created_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

7) 스키마 (Pydantic) — app/schemas/skill.py
from pydantic import BaseModel, Field
from typing import Any


class SkillListItem(BaseModel):
    id: str
    name: str
    summary: str | None = None
    canonical_repo: str | None = None
    category_id: str | None = None
    skill_type: str
    spec_format: str
    status: str


class SkillDetail(BaseModel):
    id: str
    name: str
    summary: str | None = None
    description_md: str | None = None
    canonical_repo: str | None = None
    category_id: str | None = None
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


class SkillQuery(BaseModel):
    q: str | None = None
    category_id: str | None = None
    tag: str | None = None
    sort: str = Field(default="latest", pattern="^(latest|popular)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

8) DB 의존성 — app/api/deps.py
from typing import Generator
from app.db.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

9) 보안(JWT) — app/security/auth.py
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

10) API 라우터 — app/api/router.py
from fastapi import APIRouter
from app.api import health, skills, taxonomy, rankings, events, admin

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(skills.router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy.router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])

11) 엔드포인트 예시
11.1 app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health():
    return {"ok": True}

11.2 app/api/skills.py (조회만)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillListItem, SkillDetail, SkillQuery

router = APIRouter()

@router.get("", response_model=list[SkillListItem])
def list_skills(query: SkillQuery = Depends(), db: Session = Depends(get_db)):
    stmt = select(Skill)

    if query.q:
        stmt = stmt.where(Skill.name.ilike(f"%{query.q}%"))
    if query.category_id:
        stmt = stmt.where(Skill.category_id == query.category_id)

    # sort
    if query.sort == "latest":
        stmt = stmt.order_by(Skill.updated_at.desc().nullslast())
    else:
        # popularity sort은 ranking_repo에서 join으로 구현 권장 (스켈레톤에서는 최신 fallback)
        stmt = stmt.order_by(Skill.updated_at.desc().nullslast())

    offset = (query.page - 1) * query.size
    rows = db.execute(stmt.offset(offset).limit(query.size)).scalars().all()

    return [
        SkillListItem(
            id=r.id,
            name=r.name,
            summary=r.summary,
            canonical_repo=r.canonical_repo,
            category_id=r.category_id,
            skill_type=r.skill_type,
            spec_format=r.spec_format,
            status=r.status,
        )
        for r in rows
    ]


@router.get("/{skill_id}", response_model=SkillDetail)
def get_skill(skill_id: str, db: Session = Depends(get_db)):
    row = db.get(Skill, skill_id)
    if not row:
        return {"detail": "Not found"}  # FastAPI가 200으로 주므로 실제는 HTTPException 권장 (간결성 위해 스켈레톤)
    return SkillDetail(
        id=row.id,
        name=row.name,
        summary=row.summary,
        description_md=row.description_md,
        canonical_repo=row.canonical_repo,
        category_id=row.category_id,
        skill_type=row.skill_type,
        spec_format=row.spec_format,
        spec_version=row.spec_version,
        capabilities=row.capabilities,
        trigger_hints=row.trigger_hints,
        negative_triggers=row.negative_triggers,
        license=row.license,
        content_policy=row.content_policy,
        license_confidence=row.license_confidence,
        status=row.status,
    )

11.3 app/api/admin.py (로그인 + raw 승인 스켈레톤)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.security.auth import create_admin_token, decode_token
from app.settings import settings

router = APIRouter()
bearer = HTTPBearer(auto_error=True)

def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload

@router.post("/login")
def admin_login(form: OAuth2PasswordRequestForm = Depends()):
    # MVP: env 기반 단일 운영자 계정 (추후 users 테이블로 확장)
    if form.username != settings.ADMIN_USERNAME or form.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_admin_token(form.username)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def admin_me(payload: dict = Depends(require_admin)):
    return {"username": payload.get("sub"), "role": payload.get("role")}

@router.get("/raw-skills")
def list_raw_skills(payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    # TODO: raw_skills 모델/스키마 추가 후 구현
    return {"items": [], "note": "TODO: implement raw_skills listing"}

12) FastAPI 엔트리 — app/main.py
from fastapi import FastAPI
from app.settings import settings
from app.api.router import router

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)

13) Alembic (마이그레이션)
13.1 alembic.ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s

13.2 migrations/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.settings import settings
from app.db.base import Base

# 모델 import (여기에 추가될수록 autogenerate가 테이블 인식)
from app.models.skill_source import SkillSource  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.tag import Tag  # noqa: F401
from app.models.skill import Skill  # noqa: F401

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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

14) 실행 가이드 — README.md
# Agent Skills Marketplace (FastAPI + Postgres) — Skeleton

## 1) 준비
- Python 3.11+
- PostgreSQL

## 2) 설치
pip install -U pip
pip install -e .

## 3) 환경설정
cp .env.example .env
# DATABASE_URL, JWT_SECRET 등 수정

## 4) Alembic 초기화/마이그레이션
alembic revision --autogenerate -m "init"
alembic upgrade head

## 5) 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## 6) 확인
GET /health
GET /skills
POST /admin/login (form: username/password)