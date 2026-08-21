#!/usr/bin/env python3
"""Bound epistemic Stop retries while preserving strict evidence gates.

A valid UNKNOWN/UNVERIFIED answer should not spin forever because Antigravity
replays Stop against an older or transport-shifted candidate. This wrapper lets
the existing structured/fresh/legacy gates decide first, then terminates only
when the same epistemic block repeats with the same honest weak verdict, the same
missing-proof ledger, and no new non-terminal tool evidence between attempts.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from hook_utils import emit, load_state, save_state
from structured_verdict_gate import (
    EXTERNAL_UNVERIFIED_RE,
    VISUAL_UNVERIFIED_RE,
    current_finish_values,
    current_model_content,
    latest_user_context,
    structured_verdict_object,
    transcript_call_rows,
)
from proof_freshness_gate import RUNTIME_UNVERIFIED_RE
from task_capsule import refresh_capsule
from telemetry import trace_event

HOOKS = Path(__file__).resolve().parent
NEXT_GATE = HOOKS / "structured_verdict_gate.py"
WEAK = {"UNKNOWN", "UNVERIFIED"}
EPISTEMIC_MARKERS = (
    "THALARCH STRUCTURED VERDICT GATE",
    "THALARCH FRESH PROOF GATE",
    "THALARCH EXTERNAL-STATE FINAL VERDICT GATE",
    "THALARCH VISUAL-STATE FINAL VERDICT GATE",
)


def _parse_decision(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except Exception:
            continue
        if isinstance(value, dict) and ("decision" in value or "injectSteps" in value):
            return value
    return None


def _ledger(obj: dict[str, Any]) -> list[str]:
    raw = obj.get("unverified")
    if not isinstance(raw, list):
        return []
    return [item.strip() for item in raw if isinstance(item, str) and item.strip()]


def _matches_reason(reason: str, items: list[str]) -> bool:
    lowered = reason.lower()
    if "visual" in lowered or "render" in lowered:
        return any(VISUAL_UNVERIFIED_RE.search(item) for item in items)
    if any(token in lowered for token in ("runtime", "test", "build", "lint", "typecheck", "benchmark", "execution")):
        return any(RUNTIME_UNVERIFIED_RE.search(item) for item in items)
    if any(token in lowered for token in ("external", "platform", "service", "pull request", "deploy", "release")):
        return any(EXTERNAL_UNVERIFIED_RE.search(item) for item in items)
    return bool(items)


def _normalized_reason(reason: str) -> str:
    return re.sub(r"\s+", " ", reason.strip())[:1400]


def decide_convergence(
    payload: dict[str, Any],
    delegated: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return (decision, state_to_save). Pure enough for replay/chaos tests."""
    if str(delegated.get("decision") or "").lower() != "continue":
        return delegated, {"signature": "clear", "attempts": 0, "nonterminal_count": 0}

    reason = str(delegated.get("reason") or "")
    if not any(marker in reason for marker in EPISTEMIC_MARKERS):
        return delegated, None

    user_order, _request, request_key = latest_user_context(payload)
    values: list[Any] = list(current_finish_values(payload, user_order))
    model_content = current_model_content(payload, user_order)
    if model_content:
        values.append(model_content)
    verdict = structured_verdict_object(values)
    if not isinstance(verdict, dict):
        return delegated, None

    conclusion = str(verdict.get("conclusion") or "").upper()
    items = _ledger(verdict)
    if conclusion not in WEAK or not items or not _matches_reason(reason, items):
        return delegated, None

    calls = transcript_call_rows(payload)
    nonterminal = [(order, name) for order, name, _ in calls if name.lower() != "finish"]
    nonterminal_count = len(nonterminal)
    material = "|".join(
        [request_key, conclusion, _normalized_reason(reason), *sorted(item.lower() for item in items)]
    )
    signature = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    old = load_state(payload, "stop-convergence")
    same = old.get("signature") == signature and int(old.get("nonterminal_count", -1)) == nonterminal_count
    attempts = int(old.get("attempts", 0)) + 1 if same else 1
    state = {"signature": signature, "attempts": attempts, "nonterminal_count": nonterminal_count}

    if attempts >= 2:
        return (
            {
                "decision": "stop",
                "reason": (
                    "THALARCH CONVERGENCE GUARD: the same epistemic Stop block repeated without new "
                    "tool evidence after an honest UNKNOWN/UNVERIFIED verdict with an explicit missing-proof "
                    "ledger. Terminating instead of creating a retry loop; the unresolved proposition remains "
                    f"{conclusion}."
                ),
            },
            state,
        )
    return delegated, state


def main() -> None:
    raw_payload = sys.stdin.read()
    try:
        value = json.loads(raw_payload)
        payload = value if isinstance(value, dict) else {}
    except Exception:
        payload = {}

    proc = subprocess.run(
        [sys.executable, str(NEXT_GATE), "--delegate", "proof_freshness_gate.py"],
        input=raw_payload,
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        emit({
            "decision": "continue",
            "reason": "THALARCH CONVERGENCE GUARD: downstream Stop verifier failed; preserve affected claims as UNVERIFIED.",
        })
        return

    delegated = _parse_decision(proc.stdout)
    if delegated is None:
        print(proc.stdout.strip())
        return

    decision, state = decide_convergence(payload, delegated)
    if state is not None:
        save_state(payload, "stop-convergence", state)

    user_order, _request, _key = latest_user_context(payload)
    values: list[Any] = list(current_finish_values(payload, user_order))
    model_content = current_model_content(payload, user_order)
    if model_content:
        values.append(model_content)
    verdict = structured_verdict_object(values) or {}
    conclusion = str(verdict.get("conclusion") or "")
    items = _ledger(verdict)
    refresh_capsule(payload, phase="stop", conclusion=conclusion, unverified=items)
    trace_event(
        payload,
        "stop",
        decision=decision.get("decision"),
        delegated_decision=delegated.get("decision"),
        conclusion=conclusion,
        convergence_attempts=(state or {}).get("attempts", 0),
        reason=str(decision.get("reason") or "")[:1000],
    )
    emit(decision)


if __name__ == "__main__":
    main()
