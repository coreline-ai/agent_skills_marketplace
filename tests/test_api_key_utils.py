from app.security.api_keys import (
    extract_key_prefix,
    generate_api_key_pair,
    hash_api_key,
    verify_api_key,
)
from app.repos.api_key_repo import build_api_key_header_candidates


def test_generate_api_key_pair_format_and_hash():
    plain, prefix, hashed = generate_api_key_pair()
    assert plain.startswith(prefix + "_")
    assert prefix.startswith("skm_")
    assert len(hashed) == 64
    assert verify_api_key(plain, hashed) is True


def test_extract_key_prefix():
    plain, prefix, _ = generate_api_key_pair()
    assert extract_key_prefix(plain) == prefix
    assert extract_key_prefix("invalid") == ""


def test_hash_api_key_deterministic():
    key = "skm_abcde_12345"
    assert hash_api_key(key) == hash_api_key(key)


def test_header_candidates():
    candidates = build_api_key_header_candidates("k1", "Bearer k2")
    assert candidates == ["k1", "k2"]
