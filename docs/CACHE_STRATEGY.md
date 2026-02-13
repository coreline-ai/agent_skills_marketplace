# Performance & Cache Strategy (2026)

This project now uses a layered cache strategy that matches current web performance practices:

1. API response cache headers (`Cache-Control` + `stale-while-revalidate`)
2. Next.js server runtime SWR cache for public GET requests
3. Redis L2 shared cache for public API responses (multi-instance safe)
4. Gzip compression for large JSON payloads

## What Was Changed

### 1) Public API cache headers

Implemented in `app/api/cache_headers.py` and applied to public endpoints:

- `/api/skills`, `/api/skills/search/ai`
- `/api/skills/{id}`
- `/api/plugins`
- `/api/packs`, `/api/packs/{id}`, `/api/packs/{id}/skills`
- `/api/rankings/top10`
- `/api/categories`, `/api/taxonomy/*`, `/api/tags`

Profiles:

- `PUBLIC_SEARCH_CACHE`: `public, max-age=15, s-maxage=30, stale-while-revalidate=120`
- `PUBLIC_DETAIL_CACHE`: `public, max-age=60, s-maxage=120, stale-while-revalidate=900`
- `PUBLIC_TAXONOMY_CACHE`: `public, max-age=300, s-maxage=600, stale-while-revalidate=3600`

### 2) Next.js server-side SWR cache

Implemented in `web/src/lib/api.ts`:

- Public `GET` requests (no token) are cached in-memory on the Next server
- Fresh hit: return cached value
- Stale hit: return stale immediately, refresh in background
- Miss: fetch from API and cache
- Admin/authenticated requests keep `no-store`

Disable switch:

- `NEXT_DISABLE_SERVER_CACHE=1`

### 3) Redis L2 shared cache (new)

Implemented in:

- `app/cache/redis_l2.py`
- `app/api/response_cache.py`

Applied to public endpoints:

- `/api/skills`, `/api/skills/search/ai`, `/api/skills/{id}`
- `/api/plugins`
- `/api/packs`, `/api/packs/{id}`, `/api/packs/{id}/skills`
- `/api/rankings/top10`
- `/api/categories`, `/api/taxonomy/*`, `/api/tags`

Behavior:

- L2 hit: API returns cached JSON with `X-Cache: HIT, redis-l2`
- L2 miss: API computes response, stores in Redis, returns `X-Cache: MISS`
- Fail-open: if Redis is down/unavailable, API continues without cache

Environment variables:

- `REDIS_URL` (example: `redis://redis:6379/0`)
- `REDIS_CACHE_ENABLED=true|false`
- `REDIS_CACHE_PREFIX=skills-marketplace`
- `REDIS_CACHE_TIMEOUT_MS=150`

### 4) Compression

Added `GZipMiddleware` in `app/main.py` with `minimum_size=1024`.

## Why This Helps

- Reduces duplicate DB calls during traffic bursts
- Improves TTFB on repeated page loads/navigations
- Keeps data reasonably fresh via SWR behavior
- Preserves safety for private/admin endpoints
- Shares cache across instances via Redis L2
