"""Redis-backed shared L2 cache for public API responses."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Optional
from urllib.parse import urlencode

from fastapi import Request
from redis.asyncio import Redis

from app.settings import get_settings

logger = logging.getLogger(__name__)


def build_cache_key(
    *,
    prefix: str,
    namespace: str,
    path: str,
    query_items: Iterable[tuple[str, str]],
) -> str:
    """Build a deterministic cache key from request path + query string."""
    normalized = sorted((k, v) for k, v in query_items)
    query = urlencode(normalized, doseq=True)
    suffix = path if not query else f"{path}?{query}"
    return f"{prefix}:{namespace}:{suffix}"


@dataclass
class RedisL2Config:
    enabled: bool
    url: str
    prefix: str
    timeout_ms: int


class RedisL2Cache:
    """Small wrapper around redis-py with fail-open behavior."""

    def __init__(self) -> None:
        self._client: Optional[Redis] = None
        self._config: Optional[RedisL2Config] = None

    async def init(self) -> None:
        settings = get_settings()
        self._config = RedisL2Config(
            enabled=settings.redis_cache_enabled,
            url=(settings.redis_url or "").strip(),
            prefix=(settings.redis_cache_prefix or "skills-marketplace").strip(),
            timeout_ms=max(50, int(settings.redis_cache_timeout_ms)),
        )
        if not self._config.enabled or not self._config.url:
            logger.info("Redis L2 cache disabled (missing REDIS_URL or disabled flag).")
            return

        timeout_sec = self._config.timeout_ms / 1000.0
        try:
            self._client = Redis.from_url(
                self._config.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=timeout_sec,
                socket_timeout=timeout_sec,
            )
            await self._client.ping()
            logger.info("Redis L2 cache connected.")
        except Exception as exc:
            logger.warning("Redis L2 cache init failed: %s", exc)
            self._client = None

    async def close(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.aclose()
        except Exception:
            pass
        finally:
            self._client = None

    def enabled(self) -> bool:
        return self._client is not None and self._config is not None

    def key_for_request(self, *, namespace: str, request: Request) -> Optional[str]:
        if self._config is None:
            return None
        return build_cache_key(
            prefix=self._config.prefix,
            namespace=namespace,
            path=request.url.path,
            query_items=request.query_params.multi_items(),
        )

    async def get_json(self, key: Optional[str]) -> Optional[Any]:
        if self._client is None or not key:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def set_json(self, key: Optional[str], payload: Any, ttl_seconds: int) -> None:
        if self._client is None or not key or ttl_seconds <= 0:
            return
        try:
            await self._client.set(key, json.dumps(payload, separators=(",", ":")), ex=ttl_seconds)
        except Exception:
            # Fail-open: caching errors must not impact API response flow.
            return


redis_l2_cache = RedisL2Cache()

