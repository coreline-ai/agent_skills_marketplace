from fastapi import HTTPException

from app.api.skills import (
    _build_match_reason,
    _parse_search_weights,
    _resolve_active_mode,
)


def test_parse_search_weights_defaults():
    assert _parse_search_weights("keyword", None) == (1.0, 0.0)
    assert _parse_search_weights("vector", None) == (0.0, 1.0)
    assert _parse_search_weights("hybrid", None) == (0.45, 0.55)


def test_parse_search_weights_hybrid_formats():
    assert _parse_search_weights("hybrid", "0.3,0.7") == (0.3, 0.7)
    assert _parse_search_weights("hybrid", "keyword:3,vector:1") == (0.75, 0.25)


def test_parse_search_weights_invalid():
    try:
        _parse_search_weights("hybrid", "bad-format")
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 422


def test_resolve_active_mode_fallback():
    active_mode, fallback = _resolve_active_mode("vector", "agent tools", embedding_available=False)
    assert active_mode == "keyword"
    assert fallback is True

    active_mode, fallback = _resolve_active_mode("hybrid", "agent tools", embedding_available=True)
    assert active_mode == "hybrid"
    assert fallback is False


def test_build_match_reason_variants():
    assert _build_match_reason("keyword", 1.2, 0.0, False) == "keyword relevance"
    assert _build_match_reason("vector", 0.0, 0.8, False) == "semantic vector match"
    assert _build_match_reason("hybrid", 0.8, 0.5, False) == "hybrid: keyword + vector"
    assert _build_match_reason("hybrid", 0.8, 0.0, False) == "hybrid: keyword-heavy"
    assert _build_match_reason("hybrid", 0.0, 0.7, False) == "hybrid: vector-heavy"
    assert _build_match_reason("hybrid", 0.9, 0.0, True) == "keyword match (vector fallback)"
