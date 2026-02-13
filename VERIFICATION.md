# 벡터 검색 수동 검증 가이드

자동 빌드가 너무 오래 걸릴 경우, 다음 단계에 따라 기능을 검증하세요.

## 1. Docker 빌드 상태 확인
빌드 과정에서 `sentence-transformers`와 `torch`를 설치하므로 5-10분 정도 소요될 수 있습니다.
```bash
docker-compose logs -f
```

## 2. 데이터베이스 마이그레이션 확인
서비스가 실행되면 `pgvector` 확장이 활성화되었는지 확인합니다:
```bash
docker-compose exec db psql -U app_user -d skills_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```
결과 행이 반환되어야 합니다.

## 3. 임베딩 백필(Backfill) 확인
워커(worker)가 임베딩을 생성하고 있는지 확인합니다:
```bash
docker-compose logs --tail=100 worker
```
로그에서 `Backfilled X missing embeddings` 메시지를 찾으세요.

## 4. API 테스트
검색 엔드포인트를 호출해 봅니다:
```bash
curl "http://localhost:8000/api/skills/search/ai?q=coding"
```
의미론적 유사도에 따라 정렬된 코딩 관련 결과를 받아야 합니다.
