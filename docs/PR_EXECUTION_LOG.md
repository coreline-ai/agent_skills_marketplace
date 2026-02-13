# PR Execution Log

## PR-1: 마일스톤 A (검색 이중화)
- 범위
  - 검색 파라미터(`mode`, `weights`, `limit`) 확장
  - 하이브리드/벡터/키워드 랭킹 및 fallback
  - `match_reason` 노출
  - 검색 품질 게이트 문서/벤치마크/CI
- 핵심 파일
  - `app/api/skills.py`
  - `docs/HYBRID_SEARCH.md`
  - `docs/SEARCH_QUALITY_GATE.md`
  - `scripts/benchmark_search.py`
  - `.github/workflows/ci.yml`
- 검증
  - `./scripts/benchmark_search.py --base-url http://localhost:8000/api --query coding --modes keyword,vector,hybrid --runs 30 --warmup 3 --top-n 10 --size 20`
  - 결과: keyword/vector/hybrid 모두 P95 목표 충족, 안정성 ratio 1.0000

## PR-2: 마일스톤 B (상세 즉시 실행 UX)
- 범위
  - 상세 페이지 Quick Start 강화
  - 4개 클라이언트 설치 스니펫/복사 UX
  - 모바일 레이아웃 점검
- 핵심 파일
  - `web/src/app/skills/[id]/page.tsx`
  - `web/src/components/SkillCopyCommand.tsx`
  - `web/src/components/InstallSnippetConfigurator.tsx`
- 검증
  - Lighthouse: Performance 97 / Accessibility 91
  - 모바일(390px) 스크린샷 점검

## PR-3: 마일스톤 C (신뢰 레이어)
- 범위
  - trust score/level/flags 계산/저장/노출
  - low-trust 노출 정책 적용
  - 관리자 override + 감사 로그
- 핵심 파일
  - `app/models/skill.py`
  - `app/quality/trust_score.py`
  - `app/api/admin_skills.py`
  - `app/models/skill_trust_audit.py`
  - `migrations/versions/9f4b1a2c7d3e_add_trust_and_api_key_models.py`
  - `migrations/versions/b7d9a9e6c4f2_fix_trust_last_verified_timezone.py`
- 검증
  - `POST /api/admin/skills/{id}/trust-override` 200
  - `GET /api/admin/skills/{id}/trust-audit` 200
  - 리스트/상세 trust 필드 일치 확인

## PR-4: 마일스톤 D (API 제품화)
- 범위
  - API key 발급/회전/폐기
  - scope 검사, 분당 rate limit, 일/월 usage 집계
  - `/docs/api` 문서 및 샌드박스 키 가이드
- 핵심 파일
  - `app/api/admin_api_keys.py`
  - `app/api/developer.py`
  - `app/repos/api_key_repo.py`
  - `app/security/api_keys.py`
  - `docs/DEVELOPER_API.md`
  - `web/src/app/docs/api/page.tsx`
- 검증
  - 무인증: 401 `missing_api_key`
  - 만료키: 401 `api_key_expired`
  - 권한부족: 403 `insufficient_scope`
  - 폐기키: 401 `api_key_revoked`
  - rate-limit 초과: 429 `rate_limit_exceeded`

## PR-5: 통합 리그레션 + 문서 마감
- 범위
  - 통합 빌드/테스트/배포 검증
  - 운영 롤백 문서화
  - 프론트 컴포넌트 테스트(vitest) 추가
  - 배포 체크리스트 게이트 스크립트 추가
- 핵심 파일
  - `docs/ROLLBACK.md`
  - `scripts/check_delivery_gate.py`
  - `web/vitest.config.ts`
  - `web/src/lib/skills-search.test.ts`
  - `web/src/components/SkillCard.test.tsx`
  - `web/src/components/SkillCopyCommand.test.tsx`
- 검증
  - `pytest -q` => 19 passed
  - `cd web && npm test` => 6 passed
  - `cd web && npm run build` => success
  - `docker-compose up --build -d` => success
