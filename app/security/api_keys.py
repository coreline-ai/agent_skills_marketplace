"""API key helpers: generation, hashing, prefix parsing."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Tuple


KEY_PREFIX_ROOT = "skm"


def extract_key_prefix(raw_key: str) -> str:
    parts = (raw_key or "").strip().split("_")
    if len(parts) < 3:
        return ""
    return "_".join(parts[:2])


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256((raw_key or "").encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), stored_hash or "")


def generate_api_key_pair() -> Tuple[str, str, str]:
    """Return (plain_key, key_prefix, key_hash)."""
    prefix_token = secrets.token_hex(5)
    secret = secrets.token_hex(24)
    key_prefix = f"{KEY_PREFIX_ROOT}_{prefix_token}"
    plain = f"{key_prefix}_{secret}"
    return plain, key_prefix, hash_api_key(plain)
