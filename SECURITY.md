# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Agent Skills Marketplace seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **security@coreline.ai**

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Varies based on complexity

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report.
2. **Investigation**: Our security team will investigate the issue.
3. **Updates**: We will keep you informed of the progress.
4. **Resolution**: Once resolved, we will notify you and discuss disclosure.

## Security Architecture

### Authentication & Authorization
- **JWT-based Authentication**: 관리자 인증에 JWT 토큰 사용
  - 만료 시간: **4시간** (환경 변수 `JWT_EXPIRE_MINUTES`로 조정 가능)
  - 알고리즘: HS256 (환경 변수 `JWT_ALGORITHM`으로 설정)
- **Password Hashing**: bcrypt(passlib)를 사용한 안전한 비밀번호 해싱
- **Rate Limiting**: 로그인 엔드포인트에 분당 5회 제한 적용

### Container Security
- **Non-root Execution**: API(`appuser`) 및 Web(`nextjs`) 컨테이너 모두 비루트 사용자로 실행
- **Pinned Image Tags**: 빌드 재현성과 공급망 보안을 위해 특정 이미지 버전 고정
  - API: `python:3.11.10-slim`
  - Web: `node:20.18.0-slim`

### Input Validation
- **Pydantic v2**: 모든 API 입력에 대해 스키마 기반 검증 수행
  - `max_length` 제약: 이름(200자), 설명(5000자), 콘텐츠(100,000자) 등
  - `min_length` 제약: 필수 필드의 빈 문자열 방지
- **SQL Injection Prevention**: SQLAlchemy ORM을 통한 파라미터화된 쿼리 사용

### API Documentation Protection
- **Production Mode**: `ENV=production`일 때 Swagger(`/docs`), ReDoc(`/redoc`), OpenAPI(`/openapi.json`) 자동 비활성화
- **Development Mode**: `ENV=development`일 때만 API 문서 접근 가능

### Audit Logging
관리자의 주요 활동에 대한 감사 로그를 기록합니다:
- ✅ 로그인 성공/실패 (비밀번호는 절대 기록하지 않음)
- ✅ 스킬 수집(Ingest) 트리거
- ✅ 스킬 리파싱(Reparse) 트리거
- ✅ 워커 설정 변경

### Automated Security Scanning
- **CI/CD Pipeline**: GitHub Actions를 통한 자동화된 보안 감사
  - `pip-audit`: Python 의존성 취약점 스캔
  - `npm audit`: Node.js 의존성 취약점 스캔
  - 실행 주기: 매 Push/PR + 매일 자정 (UTC)
- **Content Security**: 스킬 콘텐츠 내 잠재적 보안 위험 탐지 (`app/quality/security_scan.py`)

### CORS & Network
- **CORS**: 환경 변수 `CORS_ORIGINS`를 통한 허용 Origin 관리
- **HTTPS**: Render.com 배포 시 자동 HTTPS 적용

## Security Best Practices

### For Users

- `.env` 파일이나 시크릿을 버전 관리에 커밋하지 마세요
- API 키와 토큰을 정기적으로 교체(rotate)하세요
- 관리자 계정에 강력하고 고유한 비밀번호를 사용하세요
- 모든 의존성을 최신 상태로 유지하세요
- 프로덕션 환경에서는 반드시 `ENV=production`으로 설정하세요

### For Contributors

- 보안 코딩 관행을 따르세요
- 민감한 정보를 절대 로그에 기록하지 마세요
- 모든 사용자 입력을 검증하세요
- 데이터베이스 작업에 파라미터화된 쿼리를 사용하세요
- 의존성의 알려진 취약점을 검토하세요
- PR 제출 전 `pip-audit`와 `npm audit`를 실행하세요

## Known Security Considerations

- GitHub 토큰은 최소 권한 원칙에 따라 필요한 스코프만 부여하세요
- 관리자 자격 증명은 프로덕션 배포 전에 반드시 기본값에서 변경하세요
- 프로덕션 환경에서는 데이터베이스 연결에 SSL을 사용하세요
- JWT 시크릿 키는 최소 32자 이상의 랜덤 문자열을 사용하세요

## Security Changelog

| 날짜 | 변경 사항 |
|------|-----------|
| 2026-02-11 | Phase 2: Docker 태그 고정, `.env.example` 생성, 프로덕션 API 문서 비활성화, 감사 로그, 취약 패키지 업데이트 |
| 2026-02-11 | Phase 1: 비루트 컨테이너, 입력 검증 강화, JWT 만료 단축, 자동 보안 스캔 CI/CD |

---

Thank you for helping keep Agent Skills Marketplace and our users safe!
