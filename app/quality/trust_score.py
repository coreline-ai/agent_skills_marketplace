"""Trust score calculation for skills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class TrustProfile:
    score: float
    level: str  # ok|warning|limited
    flags: list[str]


def _freshness_score(github_updated_at: Optional[datetime]) -> float:
    if not github_updated_at:
        return 40.0
    now = datetime.now(timezone.utc)
    updated = github_updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    days = max((now - updated).days, 0)
    if days <= 30:
        return 100.0
    if days <= 90:
        return 80.0
    if days <= 180:
        return 60.0
    if days <= 365:
        return 45.0
    return 25.0


def compute_trust_profile(
    *,
    quality_score: Optional[float],
    is_verified: bool,
    is_official: bool,
    security_block: bool,
    security_severity: Optional[str],
    security_indicators: Optional[list[str]],
    github_updated_at: Optional[datetime],
    extra_flags: Optional[list[str]] = None,
) -> TrustProfile:
    """Calculate trust score/level from normalized inputs."""
    q = float(quality_score) if quality_score is not None else 50.0
    q = max(0.0, min(q, 100.0))
    freshness = _freshness_score(github_updated_at)

    verified_score = 100.0 if is_verified else 45.0
    official_score = 100.0 if is_official else 60.0

    security_score = 100.0
    severity = (security_severity or "").strip().lower()
    if security_block:
        if severity == "critical":
            security_score = 0.0
        elif severity == "high":
            security_score = 20.0
        else:
            security_score = 35.0

    score = (
        (q * 0.45)
        + (security_score * 0.25)
        + (verified_score * 0.10)
        + (official_score * 0.05)
        + (freshness * 0.15)
    )
    score = max(0.0, min(score, 100.0))

    flags: list[str] = []
    if security_block:
        flags.append(f"security:{severity or 'high'}")
    indicators = [i for i in (security_indicators or []) if isinstance(i, str) and i.strip()]
    for indicator in indicators[:10]:
        flags.append(f"indicator:{indicator.strip()}")
    for raw_flag in extra_flags or []:
        flag = str(raw_flag).strip()
        if flag:
            flags.append(flag)

    if q < 60:
        flags.append("quality:low")
    if not is_verified:
        flags.append("verification:unverified")
    if freshness < 45:
        flags.append("freshness:stale")

    deduped_flags = sorted(set(flags))
    if security_block or score < 50:
        level = "limited"
    elif score < 70:
        level = "warning"
    else:
        level = "ok"

    return TrustProfile(score=round(score, 2), level=level, flags=deduped_flags)
