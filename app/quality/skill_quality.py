"""Skill quality validation based on SKILL.md conventions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


ALLOWED_MODELS = {"haiku", "sonnet", "opus", "inherit"}

DESCRIPTION_MULTILINE_PATTERN = re.compile(r"(?mi)^\s*description\s*:\s*[>|]")


@dataclass(frozen=True)
class SkillQualityResult:
    ok: bool
    score: int
    errors: list[str]
    warnings: list[str]


def _as_str(value: Any) -> Optional[str]:
    return value.strip() if isinstance(value, str) and value.strip() else None


def validate_skill_md(
    *,
    metadata: dict[str, Any],
    body: str,
    frontmatter_raw: Optional[str],
    frontmatter_error: Optional[str],
) -> SkillQualityResult:
    """
    Validate a parsed SKILL.md.

    Notes:
    - We treat schema violations as errors (filtered out from public ingestion).
    - We treat best-practice issues as warnings (still accepted).
    """
    errors: list[str] = []
    warnings: list[str] = []
    score = 100

    if frontmatter_error:
        errors.append(frontmatter_error)
        score -= 40

    if not frontmatter_raw:
        warnings.append("missing_frontmatter")
        score -= 5
    else:
        # Known Claude Code indexing pitfall: YAML multiline indicators for description.
        if DESCRIPTION_MULTILINE_PATTERN.search(frontmatter_raw):
            errors.append("description_multiline_yaml_not_supported")
            score -= 25

    description = _as_str(metadata.get("description")) or _as_str(metadata.get("summary"))
    if not description:
        # Allow fallback to first sentence in body, but still warn.
        for line in (body or "").splitlines():
            text = line.strip()
            if not text:
                continue
            if text.startswith(("#", "-", "*", "```", ">")):
                continue
            description = text
            warnings.append("description_missing_used_body_fallback")
            score -= 10
            break

    if not description:
        errors.append("missing_description")
        score -= 30
    else:
        if len(description) < 20:
            errors.append("description_too_short")
            score -= 20
        if len(description) > 1024:
            warnings.append("description_too_long")
            score -= 5

    # Frontmatter types: enforce scalar strings for tool lists.
    for key in ("allowed-tools", "allowed_tools", "tools"):
        if key in metadata and not isinstance(metadata.get(key), str):
            errors.append(f"{key}_must_be_string")
            score -= 20

    model = _as_str(metadata.get("model"))
    if model and model.lower() not in ALLOWED_MODELS:
        errors.append("invalid_model")
        score -= 10

    # Known bug in some environments: "name" in frontmatter can break registrations.
    if "name" in metadata:
        warnings.append("frontmatter_name_field_present")
        score -= 2

    # Size guard: keep skills reasonably sized.
    body_lines = len((body or "").splitlines())
    if body_lines > 500:
        warnings.append("body_too_long")
        score -= 10

    score = max(0, min(100, score))
    ok = len(errors) == 0
    return SkillQualityResult(ok=ok, score=score, errors=errors, warnings=warnings)

