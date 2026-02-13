"""Helpers to read/write shared API response cache (Redis L2)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.cache.redis_l2 import redis_l2_cache


async def try_cached_response(
    *,
    request: Request,
    namespace: str,
    cache_control: str,
) -> Optional[JSONResponse]:
    """Return JSONResponse when Redis L2 has a cached payload."""
    if not redis_l2_cache.enabled():
        return None
    key = redis_l2_cache.key_for_request(namespace=namespace, request=request)
    payload = await redis_l2_cache.get_json(key)
    if payload is None:
        return None
    response = JSONResponse(content=payload)
    response.headers["Cache-Control"] = cache_control
    response.headers["X-Cache"] = "HIT, redis-l2"
    return response


async def set_cached_response(
    *,
    request: Request,
    namespace: str,
    payload: Any,
    ttl_seconds: int,
) -> None:
    """Write payload to Redis L2 if enabled."""
    if not redis_l2_cache.enabled():
        return
    key = redis_l2_cache.key_for_request(namespace=namespace, request=request)
    await redis_l2_cache.set_json(key, payload, ttl_seconds)

