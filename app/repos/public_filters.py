"""Shared SQL filters for publicly visible skills."""

import re
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement

from app.models.skill import Skill

PUBLIC_SKILL_URL_DB_REGEXES = (
    r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/skills/[^/]+/SKILL\.md$",
    r"^https://github\.com/[^/]+/[^/]+/blob/[^/]+/\.claude/skills/[^/]+/SKILL\.md$",
)
PUBLIC_SKILL_URL_REGEXES = (
    re.compile(r"/blob/[^/]+/skills/[^/]+/skill\.md$", re.IGNORECASE),
    re.compile(r"/blob/[^/]+/\.claude/skills/[^/]+/skill\.md$", re.IGNORECASE),
)


def public_skill_conditions() -> list[ColumnElement[bool]]:
    """Return the shared visibility policy for public APIs."""
    return [
        Skill.is_official.is_(True),
        Skill.is_verified.is_(True),
        Skill.url.is_not(None),
        or_(*[Skill.url.op("~*")(pattern) for pattern in PUBLIC_SKILL_URL_DB_REGEXES]),
    ]


def is_public_skill_url(url: Optional[str]) -> bool:
    """Runtime equivalent of public URL policy."""
    if not url:
        return False
    lowered = url.lower()
    return any(regex.search(lowered) for regex in PUBLIC_SKILL_URL_REGEXES)
