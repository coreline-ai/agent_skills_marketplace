# SKILL_PARSER.md — SKILL.md 파서 규칙 문서 (v1.0)

> AI Agent Skills Marketplace  
> SKILL.md 파일을 안전하고 일관되게 파싱하기 위한 **공식 파서 규칙 문서**

---

## 1. 문서 목적

이 문서는 다양한 형태로 존재하는 SKILL.md 파일을  
**중단 없이 수집하고, 실패를 흡수하며, 운영 가능한 수준으로 정규화**하기 위한  
파서 규칙과 판단 기준을 정의한다.

- 대상: 크롤러, 백엔드 파서, 운영자 콘솔
- 목표: 파싱 실패로 인한 데이터 유실 방지
- 원칙: “깨진 스킬도 데이터다”

---

## 2. SKILL.md 기본 개념

### 2.1 파일 정의

- 파일명: SKILL.md
- 위치:
  - 리포 루트
  - skills 디렉터리 하위
  - 복수 스킬의 경우 각 스킬 폴더별 SKILL.md 허용

### 2.2 기본 구조 (개념적)

1. YAML Frontmatter (선택)
2. Markdown Body (필수)

Frontmatter는 메타데이터 용도이며,  
본문은 인간과 에이전트가 읽는 설명 영역이다.

---

## 3. 파싱 전체 흐름

1. 파일 존재 여부 확인
2. Frontmatter 경계 탐색
3. YAML 파싱 시도
4. Markdown 본문 분리
5. 필드 정규화
6. 파싱 상태 결정
7. 결과 저장 (raw_skills)

---

## 4. Frontmatter 인식 규칙

### 4.1 경계 규칙

- 파일 최상단에 연속된 구분선 2개가 있을 경우 frontmatter로 간주
- 구분선은 다음 조건 중 하나를 만족하면 인정
  - 세 개 이상의 하이픈
  - 세 개 이상의 등호

### 4.2 인식 실패 처리

- 구분선이 하나만 존재하거나
- 중간에 다른 텍스트가 끼어 있는 경우

→ Frontmatter 없음으로 처리  
→ 전체 문서를 Markdown Body로 취급

---

## 5. YAML 파싱 규칙

### 5.1 파싱 시도 원칙

- 엄격 모드 금지
- 오류 발생 시 즉시 실패 처리하지 않음
- 가능한 필드만 추출

### 5.2 허용되는 YAML 오류

- 따옴표 미종료
- 들여쓰기 불일치
- 배열/객체 혼용
- 주석 위치 오류

→ 오류는 기록하되, 파싱은 계속 진행

---

## 6. 메타데이터 필드 규칙

### 6.1 핵심 필드 (가능하면 추출)

- name
- description
- summary
- tags
- category
- inputs
- outputs
- constraints
- triggers

### 6.2 필드 정규화 규칙

- name
  - 문자열 우선
  - 배열일 경우 첫 항목 사용
- description / summary
  - Markdown 허용
  - 길이 제한 없음
- tags
  - 문자열 또는 배열 허용
  - 쉼표 분리 문자열은 배열로 변환
- category
  - 문자열만 허용
  - 원문 그대로 category_raw에 저장

---

## 7. Markdown Body 처리 규칙

### 7.1 본문 필수성

- Frontmatter가 없어도 본문은 필수
- 본문이 완전히 비어 있으면 품질 플래그 대상

### 7.2 본문 정제

- 헤더 레벨 유지
- 코드 블럭 원문 보존
- 링크/이미지 제거하지 않음

---

## 8. 파싱 상태(parse_status) 결정 규칙

| 상태 | 조건 |
|----|----|
| valid | Frontmatter 정상 + 핵심 필드 존재 |
| partial | Frontmatter 존재하나 필드 일부 누락 |
| invalid_frontmatter | Frontmatter 인식은 됐으나 YAML 파싱 실패 |
| markdown_only | Frontmatter 없음, 본문만 존재 |
| unsupported | 파일 구조가 명백히 스펙 외 |

---

## 9. 에러 기록 규칙 (parse_errors)

- 에러는 문자열 배열로 기록
- 예:
  - yaml_parse_error
  - missing_name
  - empty_body
  - invalid_tag_format

에러는 **운영자 참고용**이며,  
자동 배제 기준으로 사용하지 않는다.

---

## 10. 다중 스킬 리포 처리 규칙

- 하나의 리포에 여러 SKILL.md가 있을 경우
  - 각각을 독립된 raw_skills 레코드로 취급
- canonical_repo는 동일하게 유지
- 병합 여부는 운영자 승인 단계에서 결정

---

## 11. 스킬 폴더 구조 탐지

### 11.1 탐지 대상 디렉터리

- scripts
- assets
- references
- examples

### 11.2 결과 저장

- capabilities 필드에 boolean 플래그로 저장
- 예:
  - scripts true
  - assets false
  - references true

---

## 12. 파싱 실패 원칙 (중요)

- 파싱 실패는 **데이터 손실 사유가 아니다**
- invalid_frontmatter / markdown_only 상태도
  - raw_skills에 저장
  - 운영자 승인 큐에 노출

---

## 13. 운영자 콘솔 연계 규칙

운영자에게 다음 정보는 반드시 노출한다:

- parse_status
- parse_errors
- 추출된 메타데이터 미리보기
- 본문 원문 미리보기

---

## 14. 향후 확장 고려

- spec_version 필드 도입
- JSON Schema 기반 검증 (선택)
- LLM 보조 파싱(보정용, 단독 사용 금지)

---

## 15. 파서 설계 철학

- 실패하지 않는 파서
- 판단은 사람에게
- 자동화는 보조 수단
- “완벽한 스킬”보다 “살아있는 생태계”

---

## 16. 문서 종료 선언

이 문서는  
AI Agent Skills Marketplace에서 SKILL.md를 다루는  
**모든 파싱 로직의 단일 기준(Single Source of Truth)** 이다.

본 문서 기준으로 파서를 구현한다.

---
