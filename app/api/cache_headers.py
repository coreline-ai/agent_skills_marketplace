"""Cache-Control helpers for public API endpoints."""

from fastapi import Response

# Query-heavy list endpoints (search, rankings).
PUBLIC_SEARCH_CACHE = "public, max-age=15, s-maxage=30, stale-while-revalidate=120"
# Detail endpoints with moderate update frequency.
PUBLIC_DETAIL_CACHE = "public, max-age=60, s-maxage=120, stale-while-revalidate=900"
# Taxonomy-like endpoints that change rarely.
PUBLIC_TAXONOMY_CACHE = "public, max-age=300, s-maxage=600, stale-while-revalidate=3600"

# Redis L2 TTLs (seconds)
REDIS_TTL_SEARCH = 30
REDIS_TTL_DETAIL = 120
REDIS_TTL_TAXONOMY = 600


def set_public_cache(response: Response, cache_control: str) -> None:
    """Set cache headers for cache-safe public endpoints."""
    response.headers["Cache-Control"] = cache_control
