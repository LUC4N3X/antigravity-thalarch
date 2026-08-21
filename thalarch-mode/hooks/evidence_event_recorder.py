#!/usr/bin/env python3
"""Record high-value tool events for the Stop evidence gate.

PreToolUse has the proposed tool name/args and a stable stepIdx. We persist a
small event ledger in the conversation artifact directory so final enforcement
does not depend on undocumented transcript internals. Each event is also bound
to the latest explicit user request so stale evidence cannot satisfy a later turn.
"""
from __future__ import annotations

import hashlib
from typing import Any

from hook_utils import args_text, emit, load_state, read_payload, save_state, transcript_steps

MAX_EVENTS = 256
USER_SOURCES = {"USER_EXPLICIT", "USER", "HUMAN"}
USER_TYPES = {"USER_INPUT", "REQUEST", "USER_MESSAGE", "HUMAN_MESSAGE"}


def _extract_user_request(content: str) -> str:
    opener = "<USER_REQUEST>"
    closer = "</USER_REQUEST>"
    start = content.find(opener)
    if start < 0:
        return content.strip()
    body_start = start + len(opener)
    end = content.find(closer, body_start)
    if end < 0:
        return content[body_start:].strip()
    return content[body_start:end].strip()


def _latest_request_text(payload: dict[str, Any]) -> str:
    candidates: list[tuple[int, str]] = []
    for fallback, step in enumerate(transcript_steps(payload)):
        source = str(step.get("source") or "").upper()
        typ = str(step.get("type") or "").upper()
        content = step.get("content")
        if not isinstance(content, str):
            continue
        if source not in USER_SOURCES and typ not in USER_TYPES:
            continue
        request = _extract_user_request(content)
        if not request:
            continue
        raw_order = step.get("step_index", step.get("stepIndex", fallback))
        try:
            order = int(raw_order)
        except Exception:
            order = fallback
        candidates.append((order, request))

    if candidates:
        return max(candidates, key=lambda item: item[0])[1]

    for key in ("userPrompt", "userMessage", "prompt", "request"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _extract_user_request(value)
    return ""


def _request_key(payload: dict[str, Any]) -> str:
    request = _latest_request_text(payload)
    return hashlib.sha256(request.encode("utf-8")).hexdigest()[:16] if request else ""


def main() -> None:
    payload = read_payload()
    call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
    name = str(call.get("name") or "").strip()
    args = call.get("args") if isinstance(call.get("args"), dict) else {}
    step = payload.get("stepIdx", -1)
    try:
        step = int(step)
    except Exception:
        step = -1

    state = load_state(payload, "evidence-events")
    events = state.get("events") if isinstance(state.get("events"), list) else []
    events.append({
        "step": step,
        "name": name,
        "argsText": args_text(args),
        "requestKey": _request_key(payload),
        "status": "proposed",
    })
    events = events[-MAX_EVENTS:]
    save_state(payload, "evidence-events", {"events": events})
    emit({"decision": "allow"})


if __name__ == "__main__":
    main()
