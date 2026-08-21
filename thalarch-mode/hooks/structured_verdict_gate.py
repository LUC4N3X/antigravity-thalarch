#!/usr/bin/env python3
"""Front-door structured verdict gate.

Antigravity can surface a final answer through direct planner content, a terminal
``finish`` tool payload, wrapper objects, fenced JSON, embedded JSON, or nested /
double-encoded strings. This gate normalizes those shapes before the existing
fresh-proof and canonical Stop gates run, so a structured epistemic verdict
cannot evade evidence/ledger checks merely because the transport shape changed.

This file deliberately does not import benchmark code. It implements the same
class of transport recovery as production hook policy.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from hook_utils import emit, tool_calls
from proof_freshness_gate import (
    EXTERNAL_STATE_RE,
    RUNTIME_STATE_RE,
    RUNTIME_UNVERIFIED_RE,
    VISUAL_STATE_RE,
    block_reason,
    current_model_content,
    is_authoritative_external_call,
    is_visual_evidence_call,
    latest_user_context,
    runtime_kind,
    successful_runtime_evidence,
    transcript_call_rows,
)

HOOKS = Path(__file__).resolve().parent
NEXT_GATE = HOOKS / "proof_freshness_gate.py"

VERDICTS = {
    "CORRECTED_PREMISE",
    "NOT_FOUND",
    "PROVEN",
    "SUPPORTED",
    "UNKNOWN",
    "UNVERIFIED",
    "DISPROVEN",
}
STRONG_VERDICTS = {"CORRECTED_PREMISE", "NOT_FOUND", "PROVEN", "SUPPORTED", "DISPROVEN"}
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
JSON_DECODER = json.JSONDecoder()
VISUAL_UNVERIFIED_RE = re.compile(
    r"\b(?:render|browser|visual|screenshot|viewport|mobile|desktop|emulator|device|pixel)\w*\b",
    re.IGNORECASE,
)
EXTERNAL_UNVERIFIED_RE = re.compile(
    r"\b(?:authoritative|platform|service|external|remote|github|gitlab|bitbucket|pull\s+request|"
    r"\bpr\b|issue|deploy|release|publication|workflow|pipeline|ci)\b",
    re.IGNORECASE,
)


def _walk_transport(value: Any, *, max_depth: int = 4) -> Iterable[dict[str, Any]]:
    """Yield dicts from direct/wrapped/fenced/embedded/double-encoded transport values."""
    if max_depth < 0:
        return

    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_transport(child, max_depth=max_depth)
        return

    if isinstance(value, list):
        for child in value:
            yield from _walk_transport(child, max_depth=max_depth)
        return

    if not isinstance(value, str) or not value.strip():
        return

    text = value.strip()
    fence = FENCE_RE.match(text)
    if fence:
        text = fence.group(1).strip()

    try:
        parsed = json.loads(text)
    except Exception:
        parsed = None

    if parsed is not None and parsed != value and max_depth > 0:
        yield from _walk_transport(parsed, max_depth=max_depth - 1)

    for start, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _end = JSON_DECODER.raw_decode(text, start)
        except Exception:
            continue
        if max_depth > 0:
            yield from _walk_transport(parsed, max_depth=max_depth - 1)


def _verdict(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip().upper()
    return normalized if normalized in VERDICTS else ""


def structured_verdict_object(values: Iterable[Any]) -> dict[str, Any] | None:
    """Return the first concrete verdict object from values ordered by finality."""
    seen: set[str] = set()
    for value in values:
        for obj in _walk_transport(value):
            conclusion = _verdict(obj.get("conclusion"))
            if not conclusion:
                continue
            try:
                marker = json.dumps(obj, ensure_ascii=False, sort_keys=True)
            except Exception:
                marker = repr(obj)
            if marker in seen:
                continue
            seen.add(marker)
            return obj
    return None


def current_finish_values(payload: dict[str, Any], user_order: int) -> list[Any]:
    finishes: list[tuple[int, Any]] = []
    for order, name, args in tool_calls(payload):
        if name.lower() != "finish":
            continue
        if user_order >= 0 and order <= user_order:
            continue
        finishes.append((order, args))
    finishes.sort(key=lambda item: item[0], reverse=True)
    return [args for _, args in finishes]


def _ledger(obj: dict[str, Any]) -> tuple[bool, list[str]]:
    if "unverified" not in obj:
        return False, []
    raw = obj.get("unverified")
    if not isinstance(raw, list):
        return True, []
    return True, [item for item in raw if isinstance(item, str) and item.strip()]


def _emit_ledger_block(kind: str, detail: str) -> None:
    emit(
        {
            "decision": "continue",
            "reason": (
                "THALARCH STRUCTURED VERDICT GATE: completion is blocked because the terminal structured "
                f"{kind} verdict does not preserve the missing proof in its unverified ledger. {detail} "
                "Wrapper/fenced/embedded/double-encoded output does not weaken the evidence contract. "
                "Rewrite the same final structured response with a concrete missing-proof entry before stopping."
            ),
        }
    )


def delegate(raw_payload: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(NEXT_GATE)],
        input=raw_payload,
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        print(proc.stdout.strip())
        return
    emit(
        {
            "decision": "continue",
            "reason": (
                "THALARCH STRUCTURED VERDICT GATE: the downstream fresh-proof verifier could not run. "
                "Do not claim verified completion; keep the affected acceptance claim UNVERIFIED."
            ),
        }
    )


def main() -> None:
    raw_payload = sys.stdin.read()
    try:
        parsed = json.loads(raw_payload)
        payload = parsed if isinstance(parsed, dict) else {}
    except Exception:
        payload = {}

    reason = str(payload.get("terminationReason") or "").lower()
    if reason in {
        "error",
        "max_steps_exceeded",
        "cancelled",
        "canceled",
        "user_cancelled",
        "user_canceled",
    }:
        delegate(raw_payload)
        return

    user_order, user_request, request_key = latest_user_context(payload)
    finish_values = current_finish_values(payload, user_order)
    model_content = current_model_content(payload, user_order)

    # Terminal finish is the strongest final-answer signal. Planner content is a fallback.
    ordered_values: list[Any] = list(finish_values)
    if model_content:
        ordered_values.append(model_content)
    verdict_obj = structured_verdict_object(ordered_values)
    if verdict_obj is None:
        delegate(raw_payload)
        return

    conclusion = _verdict(verdict_obj.get("conclusion"))
    serialized = json.dumps(verdict_obj, ensure_ascii=False, sort_keys=True)
    combined = "\n".join(part for part in (user_request, serialized) if part)
    is_external = bool(EXTERNAL_STATE_RE.search(combined))
    is_visual = bool(VISUAL_STATE_RE.search(combined))
    is_runtime = bool(RUNTIME_STATE_RE.search(combined))

    calls = transcript_call_rows(payload)
    current_calls = [row for row in calls if user_order < 0 or row[0] > user_order]

    if conclusion in STRONG_VERDICTS and is_external:
        if not any(is_authoritative_external_call(name, args) for _, name, args in current_calls):
            emit(
                {
                    "decision": "continue",
                    "reason": block_reason(
                        "structured current external-state",
                        "The terminal structured verdict has no authoritative platform/service evidence after the latest user request.",
                    ),
                }
            )
            return

    if conclusion in STRONG_VERDICTS and is_visual:
        if not any(is_visual_evidence_call(name) for _, name, _ in current_calls):
            emit(
                {
                    "decision": "continue",
                    "reason": block_reason(
                        "structured rendered visual-state",
                        "The terminal structured verdict has no browser/screenshot/device/render evidence after the latest user request.",
                    ),
                }
            )
            return

    if conclusion in STRONG_VERDICTS and is_runtime:
        kind = runtime_kind(combined)
        if not successful_runtime_evidence(payload, request_key, kind):
            emit(
                {
                    "decision": "continue",
                    "reason": block_reason(
                        f"structured runtime {kind}",
                        "The terminal structured verdict has no successful matching execution event for the latest user request.",
                    ),
                }
            )
            return

    ledger_present, items = _ledger(verdict_obj)
    if conclusion in {"UNKNOWN", "UNVERIFIED"} and ledger_present:
        if is_visual and not any(VISUAL_UNVERIFIED_RE.search(item) for item in items):
            _emit_ledger_block(
                "visual-state",
                "Name the missing render/browser/screenshot/viewport/mobile/desktop evidence explicitly.",
            )
            return
        if is_runtime and not any(RUNTIME_UNVERIFIED_RE.search(item) for item in items):
            _emit_ledger_block(
                "runtime",
                "Name the missing test/build/lint/typecheck/benchmark/runtime execution explicitly.",
            )
            return
        if is_external and not any(EXTERNAL_UNVERIFIED_RE.search(item) for item in items):
            _emit_ledger_block(
                "external-state",
                "Name the missing authoritative platform/service evidence explicitly.",
            )
            return

    delegate(raw_payload)


if __name__ == "__main__":
    main()
