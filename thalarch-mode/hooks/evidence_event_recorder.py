#!/usr/bin/env python3
"""Record high-value tool events for the Stop evidence gate.

PreToolUse has the proposed tool name/args and a stable stepIdx. We persist a
small event ledger in the conversation artifact directory so final enforcement
does not depend on undocumented transcript internals.
"""
from __future__ import annotations

from hook_utils import args_text, emit, load_state, read_payload, save_state

MAX_EVENTS = 256


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
        "status": "proposed",
    })
    events = events[-MAX_EVENTS:]
    save_state(payload, "evidence-events", {"events": events})
    emit({"decision": "allow"})


if __name__ == "__main__":
    main()
