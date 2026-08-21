#!/usr/bin/env python3
"""Deterministic adaptive-runtime profile selection for Thalarch.

Profiles are deliberately conservative heuristics, not capability claims. They
control how much review/evidence discipline is requested for the current task
without changing the underlying model or silently enabling consequential tools.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from hook_utils import transcript_steps

CRITICAL_RE = re.compile(
    r"\b(?:production|prod\b|deploy|release|publish|migration|migrate|schema\s+change|"
    r"delete\b|drop\b|truncate\b|destructive|payment|billing|credential|secret|auth(?:entication|orization)?|"
    r"security|permission|access\s+control|data\s+loss|irreversible)\b",
    re.IGNORECASE,
)
DEEP_RE = re.compile(
    r"\b(?:architecture|concurren|race\s+condition|deadlock|distributed|database|transaction|"
    r"performance|latency|memory\s+leak|multi[- ]?file|refactor|visual|responsive|screenshot|browser|"
    r"cross[- ]?platform|dependency\s+upgrade|framework\s+upgrade|ci\b|pipeline)\w*\b",
    re.IGNORECASE,
)
DELIBERATE_RE = re.compile(
    r"\b(?:implement|feature|bug|fix|debug|test|benchmark|api\b|endpoint|component|build|compile|lint|"
    r"typescript|javascript|python|kotlin|java|rust|golang|android|ios|react|compose)\w*\b",
    re.IGNORECASE,
)
DIRECT_RE = re.compile(r"\b(?:rename|typo|wording|docs?|comment|format|spelling)\w*\b", re.IGNORECASE)

PROFILE_RULES = {
    "D0": {"name": "lean", "review": "none unless evidence-sensitive", "proof": "direct deterministic check"},
    "D1": {"name": "lean", "review": "self-check", "proof": "targeted repository evidence"},
    "D2": {"name": "standard", "review": "independent review when mutation is meaningful", "proof": "targeted tests or matching evidence"},
    "D3": {"name": "strict", "review": "specialist + independent review", "proof": "integration/runtime/visual evidence as applicable"},
    "D4": {"name": "critical", "review": "specialist + independent + cold verifier", "proof": "fresh end-to-end evidence and explicit residual risk"},
}


def _extract_user_request(content: str) -> str:
    opener = "<USER_REQUEST>"
    closer = "</USER_REQUEST>"
    start = content.find(opener)
    if start < 0:
        return content.strip()
    body_start = start + len(opener)
    end = content.find(closer, body_start)
    return content[body_start : end if end >= 0 else None].strip()


def request_text(payload: dict[str, Any]) -> str:
    candidates: list[tuple[int, str]] = []
    for fallback, step in enumerate(transcript_steps(payload)):
        source = str(step.get("source") or "").upper()
        typ = str(step.get("type") or "").upper()
        content = step.get("content")
        if not isinstance(content, str):
            continue
        if source not in {"USER_EXPLICIT", "USER", "HUMAN"} and typ not in {
            "USER_INPUT", "REQUEST", "USER_MESSAGE", "HUMAN_MESSAGE"
        }:
            continue
        try:
            order = int(step.get("step_index", step.get("stepIndex", fallback)))
        except Exception:
            order = fallback
        text = _extract_user_request(content)
        if text:
            candidates.append((order, text))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    for key in ("userPrompt", "userMessage", "prompt", "request"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _extract_user_request(value)
    return ""


def classify_depth(text: str) -> str:
    compact = " ".join(text.split())
    if CRITICAL_RE.search(compact):
        return "D4"
    if DEEP_RE.search(compact):
        return "D3"
    # A bounded documentation/wording edit stays direct even when the request
    # naturally uses a verb such as "fix". Risk-bearing terms above still win.
    if len(compact) <= 180 and DIRECT_RE.search(compact):
        return "D0"
    if DELIBERATE_RE.search(compact):
        return "D2"
    return "D1"


def profile_for_payload(payload: dict[str, Any]) -> dict[str, str]:
    text = request_text(payload)
    depth = classify_depth(text)
    rules = PROFILE_RULES[depth]
    request_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""
    return {
        "depth": depth,
        "profile": rules["name"],
        "review": rules["review"],
        "proof": rules["proof"],
        "request_key": request_key,
        "request": text,
    }


def profile_message(profile: dict[str, str]) -> str:
    return (
        f"THALARCH ADAPTIVE PROFILE: {profile['depth']} / {profile['profile'].upper()}. "
        f"Review policy: {profile['review']}. Evidence policy: {profile['proof']}. "
        "Escalate depth if discovery increases risk; never downgrade a task merely to save tokens."
    )
