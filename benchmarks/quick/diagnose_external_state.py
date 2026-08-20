#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from structured_output import (
    _json_objects_from_text,
    extract_result,
    validate_structured_response,
)

HERE = Path(__file__).resolve().parent
RESULTS_ROOT = HERE.parent / "results" / "quick"
PREFERRED_KEYS = ("result", "output", "response", "content", "text", "message")
GATE_MARKER = "THALARCH EXTERNAL-STATE FINAL VERDICT GATE"


def walk(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def parse_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def response_candidates_chronological(events: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    found: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()

    def record(event_index: int, candidate: Any) -> None:
        if not isinstance(candidate, dict) or validate_structured_response(candidate):
            return
        marker = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
        if marker in seen:
            return
        seen.add(marker)
        found.append((event_index, candidate))

    for event_index, event in enumerate(events):
        for obj in walk(event):
            if isinstance(obj, dict):
                record(event_index, obj)
                for key in PREFERRED_KEYS:
                    value = obj.get(key)
                    if isinstance(value, dict):
                        record(event_index, value)
                    elif isinstance(value, str):
                        for candidate in _json_objects_from_text(value):
                            record(event_index, candidate)
            elif isinstance(obj, str):
                for candidate in _json_objects_from_text(obj):
                    record(event_index, candidate)
    return found


def all_strings(events: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for event in events:
        for obj in walk(event):
            if isinstance(obj, str):
                values.append(obj)
    return values


def truthy_marker(events: list[dict[str, Any]], marker: str) -> bool:
    lowered = marker.lower()
    return any(lowered in value.lower() for value in all_strings(events))


def decision_continue_seen(events: list[dict[str, Any]]) -> bool:
    for event in events:
        for obj in walk(event):
            if isinstance(obj, dict):
                decision = obj.get("decision")
                if isinstance(decision, str) and decision.lower() == "continue":
                    return True
            if isinstance(obj, str) and '"decision"' in obj.lower() and "continue" in obj.lower():
                return True
    return False


def _tool_name(obj: dict[str, Any]) -> str:
    for key in ("name", "tool_name", "toolName", "canonical_name", "canonicalName"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    info = obj.get("tool_info")
    if isinstance(info, dict):
        return _tool_name(info)
    return ""


def _compact(value: Any, limit: int = 1800) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = repr(value)
    text = text.replace("\r", " ").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def finish_observations(events: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    """Return compact finish-tool-bearing objects from the captured CLI stream.

    This is intentionally shape-tolerant: Antigravity has used both nested tool_info
    wrappers and direct name/tool_name objects across stream-json revisions.
    """
    found: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()
    for event_index, event in enumerate(events):
        for obj in walk(event):
            if not isinstance(obj, dict):
                continue
            if _tool_name(obj).lower() != "finish":
                continue
            marker = _compact(obj, limit=10000)
            if marker in seen:
                continue
            seen.add(marker)
            found.append((event_index, obj))
    return found


def latest_run_dir() -> Path:
    candidates = [path for path in RESULTS_ROOT.iterdir() if path.is_dir()] if RESULTS_ROOT.is_dir() else []
    if not candidates:
        raise SystemExit(f"No quick benchmark runs found under {RESULTS_ROOT}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def resolve_run_dir(value: str | None) -> Path:
    if not value:
        return latest_run_dir()
    candidate = Path(value)
    if candidate.is_dir():
        return candidate.resolve()
    by_id = RESULTS_ROOT / value
    if by_id.is_dir():
        return by_id.resolve()
    raise SystemExit(f"Run directory not found: {value}")


def diagnose_file(path: Path) -> int:
    stdout = path.read_text(encoding="utf-8", errors="replace")
    events = parse_events(stdout)
    chronological = response_candidates_chronological(events)
    selected = extract_result(events, stdout)
    gate_seen = truthy_marker(events, GATE_MARKER) or GATE_MARKER.lower() in stdout.lower()
    continue_seen = decision_continue_seen(events)
    finishes = finish_observations(events)

    print(f"\n=== {path.name} ===")
    print(f"events: {len(events)}")
    print(f"gate_marker_seen: {'YES' if gate_seen else 'NO'}")
    print(f"decision_continue_seen: {'YES' if continue_seen else 'NO'}")
    print(f"finish_observations: {len(finishes)}")
    for ordinal, (event_index, obj) in enumerate(finishes, start=1):
        print(f"  finish[{ordinal}] event={event_index}: {_compact(obj)}")
    print(f"valid_structured_candidates: {len(chronological)}")

    for ordinal, (event_index, candidate) in enumerate(chronological, start=1):
        answer = str(candidate.get("answer") or "").replace("\n", " ").strip()
        if len(answer) > 140:
            answer = answer[:137] + "..."
        print(
            f"  [{ordinal}] event={event_index} conclusion={candidate.get('conclusion')} "
            f"case_id={candidate.get('case_id')} answer={answer!r}"
        )

    selected_conclusion = selected.get("conclusion") if isinstance(selected, dict) else None
    print(f"extract_result_selected: {selected_conclusion or 'NONE'}")

    if finishes:
        print("finish_diagnosis: finish tool data is present in captured stream; inspect whether its payload carries the final structured answer/verdict.")
    else:
        print("finish_diagnosis: no finish-bearing object was found in captured stream; transcript/internal hook payload remains the only observed finish source.")

    if selected_conclusion == "CORRECTED_PREMISE":
        if any(candidate.get("conclusion") in {"UNKNOWN", "UNVERIFIED", "NOT_FOUND"} for _, candidate in chronological):
            print("diagnosis: scorer selected CORRECTED_PREMISE even though a later/alternate acceptable candidate exists; inspect extraction ordering.")
        elif gate_seen or continue_seen:
            print("diagnosis: gate activity is visible, but no corrected structured answer reached the captured stream; inspect Stop continuation behavior.")
        else:
            print("diagnosis: no gate activity is visible in captured stream. Stop trace is needed to distinguish hook timing from host propagation.")
    elif selected_conclusion:
        print("diagnosis: selected structured verdict is not CORRECTED_PREMISE.")
    else:
        print("diagnosis: no conformant structured result was isolated from this stream.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose QH-05 external-state hard-gate behavior from saved quick-run NDJSON.")
    parser.add_argument("run", nargs="?", help="Run id or run directory. Defaults to latest quick run.")
    parser.add_argument("--trial", type=int, action="append", help="Only inspect selected trial number(s). Repeatable.")
    parser.add_argument("--phase", choices=["thalarch", "native", "both"], default="thalarch")
    args = parser.parse_args()

    run_dir = resolve_run_dir(args.run)
    phases = ["native", "thalarch"] if args.phase == "both" else [args.phase]
    trials = set(args.trial or [])

    print("=== THALARCH QUICK EXTERNAL-STATE DIAGNOSTIC ===")
    print(f"run: {run_dir}")

    matched = 0
    for phase in phases:
        raw_dir = run_dir / "raw" / phase
        if not raw_dir.is_dir():
            continue
        for path in sorted(raw_dir.glob("QH-05.r*.ndjson")):
            try:
                trial = int(path.stem.split(".r", 1)[1])
            except Exception:
                trial = -1
            if trials and trial not in trials:
                continue
            matched += 1
            diagnose_file(path)

    if not matched:
        raise SystemExit("No matching QH-05 raw NDJSON files found.")


if __name__ == "__main__":
    main()
