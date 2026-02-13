# Hybrid Search Design

## Goal
- Support `keyword`, `vector`, and `hybrid` search modes in `GET /api/skills`.
- Keep ranking deterministic with a stable secondary sort.
- Fail safely: if embedding generation fails, automatically fall back to keyword mode.

## Query Parameters
- `q`: search query text.
- `mode`: `keyword | vector | hybrid` (default: `hybrid`).
- `weights`: only used for `hybrid` mode.
  - Supported formats:
    - `0.45,0.55`
    - `keyword:0.45,vector:0.55`
- `limit`: optional alias for page size.

## Ranking Formula
- Hybrid mode uses:

```text
score = keyword_score * w_keyword + vector_score * w_vector
```

- Default weights:
  - `keyword`: `1.0, 0.0`
  - `vector`: `0.0, 1.0`
  - `hybrid`: `0.45, 0.55`

## Keyword Score Components
- Name match: `1.00`
- Slug match: `0.90`
- Summary match: `0.75`
- Description match: `0.65`
- Tag match: `0.80`
- Content match: `0.20`

## Vector Score
- Uses pgvector `l2_distance`.
- Distance is converted to similarity:

```text
vector_score = 1 / (1 + l2_distance)
```

## Fallback Rule
- If `mode` is `vector` or `hybrid` and embedding generation fails:
  - Automatically switch to `keyword` mode.
  - Return `match_reason` indicating fallback.

## Stable Sort
- Search mode (`q` present):
  1. Combined score (desc)
  2. Trust level rank (ok > warning > limited/none)
  3. Trust score (desc)
  4. Popularity score (desc)
  5. `updated_at` (desc)
  6. `id` (asc)

This keeps ordering deterministic for ties.

## Match Explanation
- Each list item includes `match_reason`:
  - `keyword relevance`
  - `semantic vector match`
  - `hybrid: keyword + vector`
  - `keyword match (vector fallback)`

## Regression Baseline (2026-02-13)
Measured via `./scripts/benchmark_search.py --query coding --runs 30 --warmup 3`:

- `keyword`: P95 `164.97ms`, stability exact ratio `1.0000`
- `vector`: P95 `95.22ms`, stability exact ratio `1.0000`
- `hybrid`: P95 `224.05ms`, stability exact ratio `1.0000`
