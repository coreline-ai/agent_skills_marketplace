"""Claude Skills (SKILL.md) frontmatter parsing/validation helpers.

This module focuses on *spec-alignment*, not marketplace-specific quality scoring.
We keep it permissive by default so we can roll out strict enforcement gradually.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

# Spec: name must be lowercase letters, numbers, hyphens; max 64 chars.
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")


KNOWN_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "model",
    "context",
    "agent",
    "hooks",
}


@dataclass(frozen=True)
class ClaudeSkillSpecResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]
    derived_name: Optional[str]
    derived_description: Optional[str]


def _as_str(value: Any) -> Optional[str]:
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return None


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"true", "yes", "y", "1"}:
            return True
        if raw in {"false", "no", "n", "0"}:
            return False
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    return None


def _extract_first_paragraph(body: str) -> Optional[str]:
    """Best-effort: pick the first non-empty plain-text line."""
    for line in (body or "").splitlines():
        text = line.strip()
        if not text:
            continue
        # Skip obvious non-paragraph markdown constructs.
        if text.startswith(("#", "-", "*", "```", ">")):
            continue
        return text
    return None


def _derive_name_from_canonical_url(canonical_url: str) -> Optional[str]:
    """Derive skill directory name from canonical GitHub blob URL."""
    try:
        path = urlparse(canonical_url).path
    except Exception:
        return None
    parts = [p for p in path.split("/") if p]
    # Expect: /{owner}/{repo}/blob/{branch}/skills/{skill-name}/SKILL.md
    # or:     /{owner}/{repo}/blob/{branch}/.claude/skills/{skill-name}/SKILL.md
    if len(parts) < 7:
        return None
    lowered = [p.lower() for p in parts]
    if "skills" not in lowered:
        return None

    # Find the last "skills" occurrence (handles .claude/skills).
    idx = len(lowered) - 1 - lowered[::-1].index("skills")
    if idx + 1 >= len(parts):
        return None
    folder = parts[idx + 1].strip()
    return folder or None


def _normalize_allowed_tools(value: Any) -> tuple[Optional[list[str]], list[str], list[str]]:
    """Normalize allowed-tools into a list of strings (no validation of tool names)."""
    errors: list[str] = []
    warnings: list[str] = []

    if value is None:
        return None, errors, warnings

    items: list[str] = []
    if isinstance(value, str):
        # "Read, Grep" (canonical in docs)
        parts = [p.strip() for p in value.split(",")]
        items = [p for p in parts if p]
    elif isinstance(value, list):
        for v in value:
            if isinstance(v, str) and v.strip():
                items.append(v.strip())
            else:
                errors.append("allowed_tools_list_must_contain_strings")
                break
    else:
        errors.append("allowed_tools_must_be_string_or_list")
        return None, errors, warnings

    if not items:
        warnings.append("allowed_tools_empty")
        return [], errors, warnings

    # De-dupe but keep stable order.
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized, errors, warnings


def validate_claude_skill_frontmatter(
    *,
    metadata: dict[str, Any],
    body: str,
    canonical_url: str,
    frontmatter_raw: Optional[str],
    frontmatter_error: Optional[str],
    profile: str = "lax",
) -> ClaudeSkillSpecResult:
    """Validate + normalize Claude Skills frontmatter.

    profile:
      - lax: only hard failures are errors; everything else is warnings.
      - strict: enforce spec constraints more aggressively.
    """
    p = (profile or "lax").strip().lower()
    if p not in {"lax", "strict"}:
        p = "lax"

    errors: list[str] = []
    warnings: list[str] = []

    normalized: dict[str, Any] = {}

    if frontmatter_error:
        errors.append(frontmatter_error)

    if not frontmatter_raw:
        warnings.append("missing_frontmatter")

    if not isinstance(metadata, dict):
        # YAML might parse to a scalar/list; treat as invalid.
        errors.append("frontmatter_must_be_mapping")
        metadata = {}

    unknown_fields = [k for k in metadata.keys() if isinstance(k, str) and k not in KNOWN_FRONTMATTER_FIELDS]
    if unknown_fields and p == "strict":
        warnings.append("unknown_frontmatter_fields")
        normalized["unknown_fields"] = sorted(unknown_fields)

    name = _as_str(metadata.get("name"))
    derived_name = name or _derive_name_from_canonical_url(canonical_url)
    if name:
        if not SKILL_NAME_RE.match(name):
            # In strict mode, treat name format as a real error.
            (errors if p == "strict" else warnings).append("invalid_name_format")

    description = _as_str(metadata.get("description"))
    derived_description = description or _extract_first_paragraph(body)
    if not description and derived_description:
        warnings.append("description_missing_used_body_fallback")
    if not derived_description:
        # Spec: description is recommended; keep it a warning even in strict mode.
        warnings.append("missing_description")

    argument_hint = _as_str(metadata.get("argument-hint"))
    if argument_hint is not None:
        normalized["argument-hint"] = argument_hint

    disable_model_invocation = _as_bool(metadata.get("disable-model-invocation"))
    if disable_model_invocation is None and "disable-model-invocation" in metadata:
        (errors if p == "strict" else warnings).append("disable_model_invocation_must_be_bool")
    else:
        normalized["disable-model-invocation"] = bool(disable_model_invocation) if disable_model_invocation is not None else False

    user_invocable = _as_bool(metadata.get("user-invocable"))
    if user_invocable is None and "user-invocable" in metadata:
        (errors if p == "strict" else warnings).append("user_invocable_must_be_bool")
    else:
        normalized["user-invocable"] = bool(user_invocable) if user_invocable is not None else True

    allowed_tools_raw = metadata.get("allowed-tools")
    allowed_tools, tool_errors, tool_warnings = _normalize_allowed_tools(allowed_tools_raw)
    if tool_errors:
        (errors if p == "strict" else warnings).extend(tool_errors)
    warnings.extend(tool_warnings)
    if allowed_tools is not None:
        normalized["allowed-tools"] = allowed_tools

    model = _as_str(metadata.get("model"))
    if model is not None:
        normalized["model"] = model

    context = _as_str(metadata.get("context"))
    if context is not None:
        normalized["context"] = context
        if context != "fork":
            (errors if p == "strict" else warnings).append("context_must_be_fork_if_present")

    agent = _as_str(metadata.get("agent"))
    if agent is not None:
        normalized["agent"] = agent
        if context != "fork":
            warnings.append("agent_requires_context_fork")

    hooks = metadata.get("hooks")
    if hooks is not None:
        if isinstance(hooks, dict):
            normalized["hooks"] = hooks
        else:
            (errors if p == "strict" else warnings).append("hooks_must_be_mapping")

    # Size guidance (docs recommend ~500 lines max).
    if body and len(body.splitlines()) > 500:
        warnings.append("body_too_long")

    ok = len(errors) == 0
    return ClaudeSkillSpecResult(
        ok=ok,
        errors=errors,
        warnings=warnings,
        normalized=normalized,
        derived_name=derived_name,
        derived_description=derived_description,
    )

