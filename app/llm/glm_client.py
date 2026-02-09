"""GLM client for generating skill overviews.

This module is intentionally lightweight and optional: if GLM is not configured,
callers should skip summary generation.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx
import json

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


def _extract_json_object(text: str) -> Optional[dict[str, Any]]:
    """Best-effort: parse a JSON object from a model response."""
    if not isinstance(text, str):
        return None
    raw = text.strip()
    if not raw:
        return None
    # Strip markdown fences.
    if raw.startswith("```"):
        raw = raw.strip("`")
        # After stripping backticks, it might still contain a language hint.
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1)
    raw = raw.strip()

    # Fast path.
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except Exception:
        pass

    # Scan for the first {...} block.
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidate = raw[start : end + 1]
        try:
            value = json.loads(candidate)
            return value if isinstance(value, dict) else None
        except Exception:
            return None
    return None


def _glm_timeout_seconds(*, minimum: float = 60.0) -> float:
    """GLM requests can be slow for longer prompts; enforce a sane minimum read timeout."""
    try:
        configured = float(settings.glm_timeout_seconds)
    except Exception:
        configured = 0.0
    return max(configured, float(minimum))


async def _post_json_with_retry(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
    retries: int = 2,
) -> Optional[httpx.Response]:
    """Best-effort POST with small retry for timeouts/rate limits."""
    timeout = httpx.Timeout(timeout_seconds, connect=10.0)
    last_resp: Optional[httpx.Response] = None

    for attempt in range(max(int(retries), 1)):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.post(url, headers=headers, json=payload)
                last_resp = resp

                # Retry common transient failures.
                if resp.status_code in (408, 429, 500, 502, 503, 504):
                    if attempt < retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                return resp
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt < retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            return None
        except Exception:
            return None

    return last_resp


async def classify_skill_security(
    *,
    name: str,
    description: str,
    content: str,
    url: str,
) -> Optional[dict[str, Any]]:
    """GLM-assisted classification for malicious/hacking content.

    Returns dict with keys:
    - block: bool
    - severity: low|medium|high|critical
    - confidence: 0..1
    - reasons: list[str]
    - indicators: list[str]
    """
    if not glm_is_configured():
        return None

    system = (
        "You are a strict security reviewer for a skills marketplace.\n"
        "Your task: detect malicious, hacking, credential theft, persistence, exfiltration, or destructive content.\n"
        "Return JSON only."
    )
    excerpt = (content or "")[: int(getattr(settings, "security_scan_max_chars", 6000) or 6000)]
    user = (
        "Analyze the following SKILL.md content and decide if it must be BLOCKED from registration.\n"
        "Return STRICT JSON ONLY with fields:\n"
        "- block: boolean\n"
        "- severity: one of [low, medium, high, critical]\n"
        "- confidence: number (0 to 1)\n"
        "- reasons: array of short strings\n"
        "- indicators: array of short strings (e.g. matched patterns/keywords)\n\n"
        f"URL: {url}\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
        f"Content (excerpt):\n{excerpt}\n"
    )

    payload = {
        "model": settings.glm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
    }

    headers = {"Authorization": f"Bearer {settings.glm_api_key}", "Content-Type": "application/json"}
    url = _resolve_chat_completions_url()
    if not url:
        return None

    try:
        resp = await _post_json_with_retry(
            url=url,
            headers=headers,
            payload=payload,
            timeout_seconds=_glm_timeout_seconds(minimum=60.0),
            retries=2,
        )
        if resp is None:
            return None
        if resp.status_code != 200:
            # Keep failures quiet by default (optional module).
            return None
        data = resp.json() if resp.content else {}
        choices = data.get("choices") or (data.get("data") or {}).get("choices") or []
        if not choices:
            return None
        choice0 = choices[0] if isinstance(choices[0], dict) else {}
        message = (choice0.get("message") or {}).get("content") or choice0.get("text")
        if not isinstance(message, str):
            return None
        parsed = _extract_json_object(message)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


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
        resp = await _post_json_with_retry(
            url=url,
            headers=headers,
            payload=payload,
            timeout_seconds=_glm_timeout_seconds(minimum=60.0),
            retries=2,
        )
        if resp is None:
            return None
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
        # Detail overviews are longer than list-card summaries; allow a longer read timeout.
        resp = await _post_json_with_retry(
            url=url,
            headers=headers,
            payload=payload,
            timeout_seconds=_glm_timeout_seconds(minimum=90.0),
            retries=2,
        )
        if resp is None:
            return None
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
