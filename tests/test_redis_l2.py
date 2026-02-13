from app.cache.redis_l2 import build_cache_key


def test_build_cache_key_sorts_query_items_deterministically():
    key = build_cache_key(
        prefix="skills-marketplace",
        namespace="skills:list",
        path="/api/skills",
        query_items=[("mode", "hybrid"), ("page", "1"), ("q", "redis"), ("page", "1")],
    )
    assert key == "skills-marketplace:skills:list:/api/skills?mode=hybrid&page=1&page=1&q=redis"


def test_build_cache_key_without_query():
    key = build_cache_key(
        prefix="skills-marketplace",
        namespace="rankings:top10",
        path="/api/rankings/top10",
        query_items=[],
    )
    assert key == "skills-marketplace:rankings:top10:/api/rankings/top10"

