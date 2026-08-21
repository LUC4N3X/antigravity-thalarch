#!/usr/bin/env python3
"""Mark a previously recorded evidence event as completed or failed.

PostToolUse payloads vary by Antigravity build, so failure detection accepts the
stable top-level error plus common nested exit/return-code shapes. A command that
returned non-zero must never become successful evidence merely because the hook
itself completed.
"""
from __future__ import annotations

from typing import Any

from hook_utils import emit, load_state, read_payload, save_state

EXIT_CODE_KEYS = {"exitcode", "exit_code", "returncode", "return_code", "statuscode", "status_code"}


def _nonzero_exit(value: Any) -> str:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).replace("-", "_").lower()
            if normalized in EXIT_CODE_KEYS:
                try:
                    code = int(child)
                except Exception:
                    code = 0
                if code != 0:
                    return f"nonzero exit code {code}"
            nested = _nonzero_exit(child)
            if nested:
                return nested
    elif isinstance(value, list):
        for child in value:
            nested = _nonzero_exit(child)
            if nested:
                return nested
    return ""


def _failure_reason(payload: dict[str, Any]) -> str:
    error = str(payload.get("error") or "").strip()
    if error:
        return error
    return _nonzero_exit(payload)


def main() -> None:
    payload = read_payload()
    raw_step = payload.get("stepIdx", -1)
    try:
        step = int(raw_step)
    except Exception:
        step = -1
    failure = _failure_reason(payload)

    state = load_state(payload, "evidence-events")
    events = state.get("events") if isinstance(state.get("events"), list) else []
    for event in reversed(events):
        try:
            event_step = int(event.get("step", -2))
        except Exception:
            event_step = -2
        if event_step == step and event.get("status") == "proposed":
            event["status"] = "failed" if failure else "completed"
            if failure:
                event["error"] = failure[:1000]
            break

    save_state(payload, "evidence-events", {"events": events})
    emit({})


if __name__ == "__main__":
    main()
