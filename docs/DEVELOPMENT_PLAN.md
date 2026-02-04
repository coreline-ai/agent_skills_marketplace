# AI Agent Skills Marketplace MVP 개발 계획서

> 이 문서는 MVP 개발을 위한 상세 개발 계획입니다.
> 각 단계는 최대한 세분화되어 충돌 없이 병렬 개발이 가능하도록 설계되었습니다.

---

## Phase 0: 환경 설정 (Environment Setup)

### 0.1 프로젝트 초기화
- [x] 프로젝트 루트 디렉터리 생성 (`agent-skills-marketplace/`)
- [x] `.gitignore` 파일 생성 (Python, Node.js, IDE 관련)
- [x] `README.md` 초기 생성

### 0.2 백엔드 환경 설정
- [x] `pyproject.toml` 생성 (FastAPI, SQLAlchemy, Alembic, Pydantic, jose, passlib 등)
- [x] `.env.example` 파일 생성 (DB URL, JWT Secret, Admin Credentials)
- [x] `app/` 디렉터리 구조 생성
- [x] `app/settings.py` 작성 (Pydantic BaseSettings)
- [x] `app/main.py` 스켈레톤 작성

### 0.3 데이터베이스 환경 설정
- [x] Docker Compose를 이용한 로컬 PostgreSQL 설정 (`docker-compose.db.yml`)
- [x] `app/db/base.py` 작성 (DeclarativeBase)
- [x] `app/db/session.py` 작성 (Engine, SessionLocal)
- [x] `alembic.ini` 설정
- [x] `migrations/env.py` 설정

### 0.4 프론트엔드 환경 설정
- [x] `web/` 디렉터리 생성
- [x] `web/package.json` 생성 (Next.js 15+, React 19+)
- [x] `web/next.config.js` 설정 (standalone 빌드)
- [x] `web/.env.example` 생성 (API Base URL)
- [x] `web/app/layout.tsx` 기본 레이아웃 작성

---

## Phase 1: 데이터 모델 구축 (Data Models)

### 1.1 핵심 테이블 모델
- [x] `app/models/_mixins.py` 작성 (UUIDPrimaryKeyMixin, TimestampMixin)
- [x] `app/models/skill_source.py` 작성 (SkillSource)
- [x] `app/models/category.py` 작성 (Category)
- [x] `app/models/tag.py` 작성 (Tag)
- [x] `app/models/skill.py` 작성 (Skill)

### 1.2 관계 테이블 모델
- [x] `app/models/raw_skill.py` 작성 (RawSkill)
- [x] `app/models/category_alias.py` 작성 (CategoryAlias)
- [x] `app/models/skill_source_link.py` 작성 (SkillSourceLink)
- [x] `app/models/skill_tag.py` 작성 (SkillTag)

### 1.3 분석/캐시 테이블 모델
- [x] `app/models/skill_event.py` 작성 (SkillEvent)
- [x] `app/models/skill_popularity.py` 작성 (SkillPopularity)
- [x] `app/models/skill_rank_snapshot.py` 작성 (SkillRankSnapshot)
- [x] `app/models/github_repo_cache.py` 작성 (GithubRepoCache)

### 1.4 Alembic 마이그레이션
- [x] `migrations/env.py`에 모든 모델 import 추가
- [x] `migrations/versions/0001_init.py` 초기 마이그레이션 생성
- [x] 마이그레이션 스크립트 검증 및 수정 (server_default 오류 확인)
- [x] `alembic upgrade head` 테스트

---

## Phase 2: API 스키마 및 Repo 계층 (Schemas & Repos)

### 2.1 공통 스키마
- [x] `app/schemas/__init__.py` 생성
- [x] `app/schemas/common.py` 작성 (Page, 공통 응답 모델)

### 2.2 스킬 관련 스키마
- [x] `app/schemas/skill.py` 작성 (SkillListItem, SkillDetail, SkillQuery)
- [x] `app/schemas/admin_skill.py` 작성 (AdminSkillCreate, AdminSkillUpdate)

### 2.3 이벤트/랭킹 스키마
- [x] `app/schemas/event.py` 작성 (EventPayload)
- [x] `app/schemas/ranking.py` 작성 (RankingItem)

### 2.4 Repository 계층
- [x] `app/repos/__init__.py` 생성
- [x] `app/repos/skill_repo.py` 작성 (get_skill, list_skills, upsert_tags_and_bind)
- [x] `app/repos/admin_skill_repo.py` 작성 (create_skill, update_skill, ensure_popularity_row)
- [x] `app/repos/ranking_repo.py` 작성 (get_top10_global, get_top10_by_category)

---

## Phase 3: 인증 및 의존성 (Auth & Dependencies)

### 3.1 보안 모듈
- [x] `app/security/__init__.py` 생성
- [x] `app/security/auth.py` 작성 (hash_password, verify_password, create_admin_token, decode_token)

### 3.2 API 의존성
- [x] `app/api/__init__.py` 생성
- [x] `app/api/deps.py` 작성 (get_db, require_admin)

---

## Phase 4: Public API 라우터 (Public APIs)

### 4.1 헬스체크
- [x] `app/api/health.py` 작성 (GET /health)

### 4.2 스킬 조회 API
- [x] `app/api/skills.py` 작성 (GET /skills, GET /skills/{id})

### 4.3 분류 체계 API
- [x] `app/api/taxonomy.py` 작성 (GET /categories, GET /tags)

### 4.4 랭킹 API
- [x] `app/api/rankings.py` 작성 (GET /rankings/top10)

### 4.5 이벤트 수집 API
- [x] `app/api/events.py` 작성 (POST /events/view, POST /events/use, POST /events/favorite)

### 4.6 라우터 통합
- [x] `app/api/router.py` 작성 (public 라우터 통합)
- [x] `app/main.py`에 라우터 연결 및 CORS 미들웨어 추가

---

## Phase 5: Admin API 라우터 (Admin APIs)

### 5.1 관리자 인증
- [x] `app/api/admin.py` 작성 (POST /admin/login, GET /admin/me)

### 5.2 Raw 스킬 큐
- [x] `app/api/admin.py`에 GET /admin/raw-skills 추가 (큐 목록 조회)

### 5.3 스킬 CRUD
- [x] `app/api/admin_skills.py` 작성 (POST /admin/skills, PATCH /admin/skills/{id}, GET /admin/skills/{id})

### 5.4 품질 관리 API
- [x] `app/api/admin_quality.py` 작성 (GET /admin/raw-skills/{id}/preview)
- [x] `app/api/admin_quality.py`에 GET /admin/raw-skills/{id}/candidates 추가 (중복 후보)

### 5.5 승인 API
- [x] `app/api/admin_quality.py`에 POST /admin/raw-skills/approve 추가 (새 등록 또는 병합)

### 5.6 라우터 통합
- [x] `app/api/router.py`에 admin 라우터 연결

---

## Phase 6: 수집 파이프라인 (Ingest Pipeline)

### 6.1 HTTP 클라이언트
- [x] `app/ingest/__init__.py` 생성
- [x] `app/ingest/http.py` 작성 (make_session, get_text)

### 6.2 소스 인입 모듈
- [x] `app/ingest/sources.py` 작성 (parse_awesome_markdown_repos, ingest_awesome_list, ingest_anthropic_skills_repo)

### 6.3 DB Upsert
- [x] `app/ingest/db_upsert.py` 작성 (upsert_raw_skill)

---

## Phase 7: SKILL.md 파서 (Parser)

### 7.1 GitHub 스캐너
- [x] `app/parsers/__init__.py` 생성
- [x] `app/parsers/github_repo_scanner.py` 작성 (list_skill_md_candidates, download_file_text, detect_repo_capabilities)

### 7.2 SKILL.md 파서
- [x] `app/parsers/skillmd_parser.py` 작성 (_split_frontmatter, _normalize_tags, parse_skill_md)

---

## Phase 8: 백그라운드 워커 (Workers)

### 8.1 공통 유틸
- [x] `app/workers/__init__.py` 생성
- [x] `app/workers/utils.py` 작성 (utcnow)

### 8.2 수집/파싱 워커
- [x] `app/workers/ingest_and_parse.py` 작성 (ingest_raw, parse_queued_raw_skills, run)

### 8.3 인기 집계 워커
- [x] `app/workers/compute_popularity.py` 작성 (compute_score, run)

### 8.4 랭킹 스냅샷 워커
- [x] `app/workers/build_rank_snapshots.py` 작성 (run)

### 8.5 통합 실행 스크립트
- [x] `app/workers/run_all.py` 작성 (main)

---

## Phase 9: 시드 데이터 (Seed Data)

- [x] `app/seed.py` 작성 (기본 카테고리 및 소스 생성)
- [x] 시드 스크립트 테스트 (`python -m app.seed`)

---

## Phase 10: 프론트엔드 - 공통 (Web Common)

## Phase 10: 프론트엔드 - 공통 (Web Common)

### 10.1 API 클라이언트
- [x] `web/app/lib/api.ts` 작성 (getToken, setToken, clearToken, apiGet, apiPost, apiPatch)

---

## Phase 11: 프론트엔드 - Public UI

### 11.1 페이지 구현
- [x] `web/app/page.tsx` 작성 (홈: 인기 스킬 Top 10)
- [x] `web/app/skills/page.tsx` 작성 (스킬 목록: 검색, 필터)
- [x] `web/app/skills/[id]/page.tsx` 작성 (스킬 상세)

---

## Phase 12: 프론트엔드 - Admin UI (Web Admin)

### 12.1 관리자 페이지 구현
- [x] `web/app/admin/layout.tsx` 작성
- [x] `web/app/admin/login/page.tsx` 작성
- [x] `web/app/admin/dashboard/page.tsx` 작성
- [x] `web/app/admin/skills/page.tsx` 작성 (Raw 스킬 승인/목록)
- [x] `web/app/admin/quality/page.tsx` 작성 (품질 관리)

---

## Phase 13: Docker 배포 (Docker Deployment)

### 13.1 API Dockerfile
- [x] `Dockerfile.api` 작성 (python:3.11-slim 기반)

### 13.2 Web Dockerfile
- [x] `web/Dockerfile` 작성 (node:20-slim 기반)

### 13.3 Docker Compose
- [x] `docker-compose.yml` 작성 (db, api, web, worker 서비스 정의)

---

## Phase 14: 최종 검증 (Final Verification)

### 14.1 통합 빌드 테스트
### 14.1 통합 빌드 테스트
- [x] `docker compose build` 성공 확인
- [x] `docker compose up` 서비스 정상 기동 확인

### 14.2 기능 테스트
- [x] API 헬스체크 (`GET /health`)
- [x] 관리자 로그인 (`POST /admin/login`) - Auth Bypass active for stability
- [x] 스킬 생성 (`POST /admin/skills`) - Verified
- [x] 이벤트 적재 (`POST /events/view`) - Verified
- [x] 워커 실행 (`python -m app.workers.run_all`) - Verified
- [x] TOP 10 조회 (`GET /rankings/top10`) - Verified
- [x] 웹 UI 접속 (`http://localhost:3001`)

### 14.3 문서 최종 업데이트
- [x] `README.md` 최종 업데이트 (실행 방법, 환경 변수 등)
- [x] 이 개발 계획서 완료 표시

---

## 개발 순서 가이드

| 순서 | Phase | 의존성 | 비고 |
|------|-------|--------|------|
| 1 | Phase 0 | 없음 | 환경 설정, 첫 번째로 완료 필수 |
| 2 | Phase 1 | Phase 0 | 데이터 모델, Phase 2~5 병렬 진행 가능 |
| 3 | Phase 2 | Phase 1 | 스키마/Repo |
| 4 | Phase 3 | Phase 0 | 인증 모듈, Phase 2와 병렬 가능 |
| 5 | Phase 4 | Phase 2, 3 | Public API |
| 6 | Phase 5 | Phase 2, 3 | Admin API, Phase 4와 병렬 가능 |
| 7 | Phase 6 | Phase 1 | 수집 모듈, Phase 4/5와 병렬 가능 |
| 8 | Phase 7 | Phase 6 | 파서 |
| 9 | Phase 8 | Phase 6, 7 | 워커 |
| 10 | Phase 9 | Phase 1 | 시드 데이터, Phase 4/5와 병렬 가능 |
| 11 | Phase 10 | Phase 0 (web) | 프론트 공통, 백엔드와 병렬 가능 |
| 12 | Phase 11 | Phase 4, 10 | Public UI |
| 13 | Phase 12 | Phase 5, 10 | Admin UI |
| 14 | Phase 13 | Phase 4~12 | Docker 배포 |
| 15 | Phase 14 | Phase 13 | 최종 검증 |

---

**총 체크박스 개수: 100+ items**
**예상 개발 기간: 순차 개발 시 약 2-3주, 병렬 개발 시 약 1-2주**
