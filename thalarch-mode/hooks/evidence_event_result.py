#!/usr/bin/env python3
"""Mark a previously recorded evidence event as completed or failed."""
from __future__ import annotations

from hook_utils import emit, load_state, read_payload, save_state


def main() -> None:
    payload = read_payload()
    raw_step = payload.get("stepIdx", -1)
    try:
        step = int(raw_step)
    except Exception:
        step = -1
    error = str(payload.get("error") or "").strip()

    state = load_state(payload, "evidence-events")
    events = state.get("events") if isinstance(state.get("events"), list) else []
    for event in reversed(events):
        try:
            event_step = int(event.get("step", -2))
        except Exception:
            event_step = -2
        if event_step == step and event.get("status") == "proposed":
            event["status"] = "failed" if error else "completed"
            if error:
                event["error"] = error[:1000]
            break

    save_state(payload, "evidence-events", {"events": events})
    emit({})


if __name__ == "__main__":
    main()
