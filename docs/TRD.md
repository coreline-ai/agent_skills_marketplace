# TRD.md — AI Agent Skills Marketplace (v1.0)

> Technical Requirements Document  
> PRD.md를 구현하기 위한 기술적 요구사항 및 설계 기준 문서

---

## 1. 문서 목적

이 문서는 **AI Agent Skills Marketplace**를 구현하기 위해 필요한  
기술 스택, 시스템 구성, 데이터 흐름, API 설계 원칙, 배치/운영 기준을 정의한다.

- 대상 독자: 백엔드/프론트엔드/플랫폼 개발자
- 범위: MVP 구현 + 안정적 운영
- 비범위: 비즈니스 정책, 마케팅 전략

---

## 2. 시스템 전체 아키텍처

### 2.1 구성 요소

1. Frontend Web
   - Next.js 기반 SPA/SSR
   - 사용자/운영자 UI 제공

2. Backend API
   - FastAPI 기반 REST API
   - 스킬/태그/카테고리/랭킹/운영 기능 제공

3. Crawler / Ingest Pipeline
   - Python 기반 배치 작업
   - 외부 소스 크롤링 및 raw 데이터 적재

4. Database
   - PostgreSQL (주 저장소)
   - Redis (랭킹/통계 캐시)

5. External APIs
   - GitHub API (repo 메타데이터)

---

## 3. 기술 스택

### 3.1 프론트엔드

- Framework: Next.js
- Language: TypeScript
- Styling: Tailwind CSS
- Data Fetching: REST API
- State Management: React Query 또는 SWR

---

### 3.2 백엔드

- Language: Python 3.11+
- Framework: FastAPI
- ORM: SQLAlchemy 또는 SQLModel
- Validation: Pydantic
- Auth (운영자): 간단한 JWT 또는 세션 기반

---

### 3.3 크롤러

- Language: Python
- HTTP: requests
- Parsing:
  - HTML: BeautifulSoup
  - Markdown: markdown parser
- GitHub 연동:
  - REST API
  - ETag / If-Modified-Since 사용

---

### 3.4 인프라

- Frontend: Vercel
- Backend: Render / Fly.io / PaaS
- DB: Managed PostgreSQL
- Batch: Docker + cron 또는 GitHub Actions

---

## 4. 데이터 계층 설계 원칙

### 4.1 Raw vs Canonical 분리

- raw_skills:
  - 외부 소스 그대로 저장
  - 파싱 실패도 보존
- skills:
  - 운영자 승인 후 노출
  - 사용자 신뢰 대상

---

### 4.2 정규화 전략

- 카테고리/태그는 정규화 테이블 사용
- 소스별 raw 카테고리는 alias 테이블로 매핑
- 스킬 중복은 canonical_repo + 운영자 병합으로 해결

---

## 5. 크롤링 및 인입 파이프라인

### 5.1 크롤러 구조

- 소스별 독립 모듈
- 공통 인터페이스:
  - fetch()
  - normalize()
  - upsert_raw()

---

### 5.2 인입 흐름

1. 외부 소스 접근
2. 목록/리포 파싱
3. raw_skills upsert
4. 변경 감지(source_revision 비교)
5. 신규/변경 스킬 큐 반영

---

### 5.3 GitHub API 최적화

- repo 단위 캐시 테이블 사용
- 하루 1회 메타데이터 갱신
- ETag 기반 조건부 요청
- 실패 상태(fetch_status) 기록

---

## 6. SKILL.md 파싱 규칙

### 6.1 파싱 대상

- SKILL.md
- skills 디렉터리 하위 SKILL.md
- markdown_only 문서

---

### 6.2 파싱 결과 상태

- valid
- partial
- invalid_frontmatter
- markdown_only
- unsupported

---

### 6.3 파싱 실패 처리

- raw 데이터 유지
- parse_errors 기록
- 운영자 승인 대기 큐로 이동

---

## 7. API 설계 원칙

### 7.1 공통 원칙

- RESTful 설계
- 명확한 리소스 단위
- 읽기 API는 공개 가능
- 운영자 API는 인증 필수

---

### 7.2 주요 API 그룹

1. Public API
   - GET /skills
   - GET /skills/{id}
   - GET /categories
   - GET /tags
   - GET /rankings/top10

2. Event API
   - POST /events/view
   - POST /events/use
   - POST /events/favorite

3. Admin API
   - GET /admin/raw-skills
   - POST /admin/skills/approve
   - POST /admin/skills/merge
   - POST /admin/skills/ignore

---

## 8. 이벤트 수집 및 집계

### 8.1 이벤트 정의

- view: 상세 페이지 조회
- use: 링크 클릭
- favorite: 즐겨찾기

---

### 8.2 개인정보 최소화

- session_hash
- ip_hash
- ua_hash
- 원본 IP/User-Agent 저장 금지

---

### 8.3 집계 정책

- 동일 세션 반복 이벤트 제외
- 집계 결과는 skill_popularity에 저장
- 랭킹 계산은 배치 작업으로 수행

---

## 9. 랭킹 및 캐시 전략

### 9.1 랭킹 계산

- 하루 1회 이상 배치
- GitHub 지표 + 내부 이벤트 가중치 적용
- 최근성 보너스 적용

---

### 9.2 랭킹 스냅샷

- skill_rank_snapshots 테이블에 저장
- UI는 스냅샷 기준으로 노출
- 캐시 미스 시 DB 조회

---

## 10. 운영자 콘솔 기술 요구사항

- 승인 대기 큐 페이지네이션
- 잠재 중복 후보 계산(이름 + 설명 유사도)
- 파싱 상태/라이선스/스크립트 여부 시각화
- 모든 운영 액션은 로그로 남김

---

## 11. 보안 및 안정성

### 11.1 보안

- scripts 포함 스킬은 기본 link_only
- 악성 repo 블랙리스트 구조 유지
- 외부 입력 데이터는 전부 검증

---

### 11.2 안정성

- 외부 API 실패 시 재시도/백오프
- 크롤러 실패는 전체 파이프라인 중단 금지
- 중요 배치 작업 알림 연동

---

## 12. 테스트 전략

### 12.1 테스트 종류

- Unit Test
- API Integration Test
- 크롤러 Mock Test
- 파싱 실패 케이스 테스트

---

### 12.2 MVP 기준

- 핵심 API 정상 응답
- 최소 3개 소스 크롤링 성공
- 승인 → 노출 플로우 통과
- TOP 10 계산 정상

---

## 13. 기술적 비전

- API First 구조 유지
- IDE/Agent Runtime 연동 고려한 설계
- LLM 파이프라인 추가 가능한 확장성 확보

---

## 14. TRD 종료 선언

이 문서는 PRD.md의 모든 기능 요구사항을  
**구현 가능한 기술 설계 수준**으로 구체화한다.

본 문서 기준으로 개발을 시작할 수 있다.

---
