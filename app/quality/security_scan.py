"""Security scan for ingested SKILL.md content.

Goal: prevent obvious malicious / hacking / destructive instructions from being registered.

This is a lightweight heuristic scan that can be augmented with GLM classification.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SecurityScanResult:
    ok: bool
    severity: str  # low|medium|high|critical
    confidence: float
    reasons: list[str]
    indicators: list[str]
    content_sha1: str
    provider: str  # heuristic|glm

    @property
    def block(self) -> bool:
        return not self.ok


_DANGEROUS_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    # Match "rm -rf /" even when embedded in prose (e.g. "Run: sudo rm -rf /").
    # Keep it specific to the root path to avoid false positives like "rm -rf /tmp".
    (
        "destructive_rm",
        re.compile(r"\b(sudo\s+)?rm\s+-(?:rf|fr)\s+/(?:\s|$|\*)", re.IGNORECASE),
        "Destructive rm -rf /",
    ),
    ("disk_wipe_dd", re.compile(r"\bdd\s+if=/dev/(zero|random)\b", re.IGNORECASE), "Disk wipe via dd"),
    ("mkfs", re.compile(r"\bmkfs\.(ext[234]|xfs|btrfs)\b", re.IGNORECASE), "Filesystem formatting (mkfs.*)"),
    ("curl_pipe_sh", re.compile(r"\bcurl\b[^\n]*\|\s*(bash|sh)\b", re.IGNORECASE), "Remote script execution (curl | sh)"),
    ("wget_pipe_sh", re.compile(r"\bwget\b[^\n]*\|\s*(bash|sh)\b", re.IGNORECASE), "Remote script execution (wget | sh)"),
    ("reverse_shell_tcp", re.compile(r"/dev/tcp/\d{1,3}(?:\.\d{1,3}){3}/\d{2,5}", re.IGNORECASE), "Reverse shell via /dev/tcp"),
    ("netcat_exec", re.compile(r"\bnc\b[^\n]*\s+-e\s+\S+", re.IGNORECASE), "Netcat remote exec (-e)"),
    ("chmod_suid", re.compile(r"\bchmod\b[^\n]*\s+\+s\s+\S+", re.IGNORECASE), "SUID bit set (chmod +s)"),
    ("ssh_authorized_keys", re.compile(r"authorized_keys", re.IGNORECASE), "Writes/mentions SSH authorized_keys (persistence risk)"),
    ("exfil_env", re.compile(r"\b(printenv|env)\b[^\n]*\|\s*(curl|wget)\b", re.IGNORECASE), "Potential environment exfiltration"),
]

_HACKING_KEYWORDS = [
    "credential dump",
    "steal credentials",
    "keylogger",
    "phishing",
    "exploit",
    "payload",
    "reverse shell",
    "privilege escalation",
    "dump passwords",
    "token theft",
]


def _sha1(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8", errors="ignore")).hexdigest()


def heuristic_security_scan(
    *,
    name: str,
    description: str,
    content: str,
    url: Optional[str] = None,
) -> SecurityScanResult:
    """Heuristic scan. Conservative: blocks obvious dangerous payloads/commands."""
    text = "\n".join([name or "", description or "", content or "", url or ""]).strip()
    sha = _sha1(text)
    lowered = text.lower()

    indicators: list[str] = []
    reasons: list[str] = []

    for key, pattern, reason in _DANGEROUS_PATTERNS:
        if pattern.search(text):
            indicators.append(key)
            reasons.append(reason)

    for kw in _HACKING_KEYWORDS:
        if kw in lowered:
            indicators.append(f"kw:{kw.replace(' ', '_')}")
            reasons.append(f"Suspicious hacking keyword: {kw}")

    if indicators:
        # Escalate severity based on the most dangerous classes.
        critical_keys = {"destructive_rm", "disk_wipe_dd", "mkfs", "reverse_shell_tcp", "netcat_exec", "chmod_suid"}
        severity = "critical" if any(k in critical_keys for k in indicators) else "high"
        confidence = 0.95 if severity == "critical" else 0.8
        return SecurityScanResult(
            ok=False,
            severity=severity,
            confidence=confidence,
            reasons=sorted(set(reasons)),
            indicators=sorted(set(indicators)),
            content_sha1=sha,
            provider="heuristic",
        )

    return SecurityScanResult(
        ok=True,
        severity="low",
        confidence=0.2,
        reasons=[],
        indicators=[],
        content_sha1=sha,
        provider="heuristic",
    )
