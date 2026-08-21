#!/usr/bin/env python3
"""Request-scoped durable task state for safe context recovery.

The capsule is intentionally compact: it preserves the current request identity,
adaptive profile, recent evidence outcomes, and final uncertainty. It is not a
long-term memory store and is reset whenever the explicit user request changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hook_utils import load_state, save_state
from runtime_profile import profile_for_payload

MAX_EVENTS = 12


def _event_summary(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": event.get("step"),
        "name": str(event.get("name") or "")[:120],
        "status": str(event.get("status") or "")[:40],
        "error": str(event.get("error") or "")[:240],
    }


def refresh_capsule(
    payload: dict[str, Any],
    *,
    phase: str,
    conclusion: str = "",
    unverified: list[str] | None = None,
) -> dict[str, Any]:
    profile = profile_for_payload(payload)
    current = load_state(payload, "task-capsule")
    if current.get("request_key") != profile["request_key"]:
        current = {
            "schema_version": 1,
            "request_key": profile["request_key"],
            "request": profile["request"][:1200],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    evidence_state = load_state(payload, "evidence-events")
    raw_events = evidence_state.get("events") if isinstance(evidence_state.get("events"), list) else []
    summaries = [_event_summary(item) for item in raw_events if isinstance(item, dict)][-MAX_EVENTS:]

    current.update(
        {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "depth": profile["depth"],
            "profile": profile["profile"],
            "recent_evidence": summaries,
        }
    )
    if conclusion:
        current["conclusion"] = conclusion
    if unverified is not None:
        current["unverified"] = [str(item)[:400] for item in unverified[:12]]
    save_state(payload, "task-capsule", current)
    return current


def capsule_message(payload: dict[str, Any]) -> str:
    profile = profile_for_payload(payload)
    current = load_state(payload, "task-capsule")
    if not current or current.get("request_key") != profile["request_key"]:
        return ""
    evidence = current.get("recent_evidence") if isinstance(current.get("recent_evidence"), list) else []
    compact = ", ".join(
        f"{str(item.get('name') or '?')}={str(item.get('status') or '?')}"
        for item in evidence[-6:]
        if isinstance(item, dict)
    )
    unresolved = current.get("unverified") if isinstance(current.get("unverified"), list) else []
    parts = [f"THALARCH TASK CAPSULE: request={profile['request_key']} profile={profile['depth']}/{profile['profile']}."]
    if compact:
        parts.append(f"Recent evidence: {compact}.")
    if unresolved:
        parts.append("Outstanding proof: " + "; ".join(str(item) for item in unresolved[:4]) + ".")
    parts.append("Treat this capsule as continuity metadata only; current repository/tool evidence still wins.")
    return " ".join(parts)
