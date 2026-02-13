# Search Quality Gate

## Scope
- Endpoint: `GET /api/skills`
- Modes: `keyword`, `vector`, `hybrid`
- Query params used for gate: `q`, `mode`, `size=20`, `page=1`

## Target SLO (Staging)
- Latency target (P95):
  - `keyword`: `<= 350ms`
  - `vector`: `<= 700ms`
  - `hybrid`: `<= 650ms`
- Ordering stability target (same query, repeated runs):
  - `keyword`: top-10 exact order match ratio `>= 0.95`
  - `vector`: top-10 exact order match ratio `>= 0.80`
  - `hybrid`: top-10 exact order match ratio `>= 0.85`

## How To Measure

Run benchmark script from repository root:

```bash
./scripts/benchmark_search.py \
  --base-url http://localhost:8000/api \
  --query coding \
  --modes keyword,vector,hybrid \
  --runs 30 \
  --warmup 3 \
  --top-n 10 \
  --size 20
```

JSON output mode:

```bash
./scripts/benchmark_search.py --json
```

## Pass/Fail Decision
- Pass when:
  - each mode P95 is within target
  - each mode ordering stability ratio is within target
- Fail when either latency or stability misses target.

## Regression Baseline Process
- Save benchmark output artifact per PR.
- Compare with previous `main` baseline.
- If deviation is large:
  - inspect query plan and index usage
  - inspect embedding generation failures / fallback rate
  - adjust weight defaults only with explicit release note

## Notes
- Final checklist completion still requires staging verification.
