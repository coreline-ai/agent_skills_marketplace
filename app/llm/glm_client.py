"""GLM client for generating skill overviews.

This module is intentionally lightweight and optional: if GLM is not configured,
callers should skip summary generation.
"""

from __future__ import annotations

from typing import Optional

import httpx

from app.settings import get_settings

settings = get_settings()


def glm_is_configured() -> bool:
    base = settings.glm_chat_completions_url or settings.glm_api_base
    return bool(settings.glm_api_key and base and settings.glm_model)


def _resolve_chat_completions_url() -> str:
    """
    Resolve the actual endpoint to call.
    Users often provide a "base" URL (e.g. .../v4) rather than the final
    OpenAI-compatible chat-completions path.
    """
    url = (settings.glm_chat_completions_url or settings.glm_api_base or "").strip()
    if not url:
        return ""
    lowered = url.lower().rstrip("/")
    if lowered.endswith("/chat/completions") or lowered.endswith("/completions"):
        return url
    return f"{url.rstrip('/')}/chat/completions"


async def summarize_skill_overview(*, name: str, description: str, content: str) -> Optional[str]:
    """
    Produce a short overview summary for list cards.
    Returns None when GLM is not configured or if the request fails.
    """
    if not glm_is_configured():
        return None

    # Keep prompt short; we want a compact list-card line, not a re-write.
    system = "You write concise one-paragraph overviews for skill catalog cards."
    user = (
        "Summarize this skill for a marketplace list card.\n"
        "Constraints: 1 sentence, <= 140 characters, plain text, no emojis.\n\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
        f"Content (excerpt): {content[:1200]}\n"
    )

    payload = {
        "model": settings.glm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": float(settings.glm_temperature),
    }

    headers = {"Authorization": f"Bearer {settings.glm_api_key}", "Content-Type": "application/json"}
    url = _resolve_chat_completions_url()
    if not url:
        return None

    try:
        timeout = httpx.Timeout(float(settings.glm_timeout_seconds), connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json() if resp.content else {}
            # Try to support OpenAI-like response format (and a few variants).
            choices = data.get("choices") or (data.get("data") or {}).get("choices") or []
            if not choices:
                return None
            choice0 = choices[0] if isinstance(choices[0], dict) else {}
            message = (choice0.get("message") or {}).get("content") or choice0.get("text")
            if not isinstance(message, str):
                return None
            text = message.strip().replace("\n", " ")
            return text[:200] if text else None
    except Exception:
        return None


async def summarize_skill_detail_overview(*, name: str, description: str, content: str) -> Optional[str]:
    """
    Produce a markdown overview for the skill detail page.
    Returns None when GLM is not configured or if the request fails.
    """
    if not glm_is_configured():
        return None

    system = "You summarize SKILL.md content for a marketplace detail page."
    user = (
        "Write an 'Overview' section for this skill.\n"
        "Format: markdown only.\n"
        "Constraints:\n"
        "- 4 to 7 bullet points\n"
        "- Each bullet <= 120 characters\n"
        "- Mention what it does, key capabilities, and any important constraints\n"
        "- No emojis\n\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
        f"SKILL.md (excerpt): {content[:2400]}\n"
    )

    payload = {
        "model": settings.glm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": float(settings.glm_temperature),
    }

    headers = {"Authorization": f"Bearer {settings.glm_api_key}", "Content-Type": "application/json"}
    url = _resolve_chat_completions_url()
    if not url:
        return None

    try:
        timeout = httpx.Timeout(float(settings.glm_timeout_seconds), connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json() if resp.content else {}
            choices = data.get("choices") or (data.get("data") or {}).get("choices") or []
            if not choices:
                return None
            choice0 = choices[0] if isinstance(choices[0], dict) else {}
            message = (choice0.get("message") or {}).get("content") or choice0.get("text")
            if not isinstance(message, str):
                return None
            text = message.strip()
            # Avoid runaway responses; this should be a small markdown block.
            return text[:2000] if text else None
    except Exception:
        return None
