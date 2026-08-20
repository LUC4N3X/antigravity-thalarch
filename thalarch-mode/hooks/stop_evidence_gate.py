#!/usr/bin/env python3
"""Prevent final output from outrunning the evidence actually observed.

Primary evidence comes from the hook event ledger written by PreToolUse/PostToolUse.
Transcript parsing is retained both for final-answer epistemic checks and as a
backward-compatible fallback for conversations that began before the event recorder
was installed.
"""
from __future__ import annotations

import json
import re
from typing import Any

from hook_utils import emit, latest_model_content, load_state, read_payload, save_state, tool_calls

MUTATOR_AGENTS = {
    "thalarch-implementer",
    "thalarch-java-engineer",
    "thalarch-kotlin-engineer",
    "thalarch-python-engineer",
    "thalarch-typescript-engineer",
    "thalarch-go-engineer",
    "thalarch-rust-engineer",
    "thalarch-web-designer",
    "thalarch-visual-director",
}

STRONG_EXTERNAL_VERDICTS = {"CORRECTED_PREMISE", "NOT_FOUND", "PROVEN", "SUPPORTED"}
EXTERNAL_STATE_RE = re.compile(
    r"(?ix)"
    r"\b(?:pull\s+request|pr\b|issue\s+#?\d+|issue\s+url|"
    r"deploy(?:ment)?\s+(?:state|status|url|live)|"
    r"release\s+(?:state|status|url|live|published)|"
    r"publication\s+(?:state|status|url|live|published)|"
    r"remote\s+(?:state|object|url)|platform\s+url)\b|"
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/"
)
CONCLUSION_RE = re.compile(
    r"(?i)[\"']?conclusion[\"']?\s*[:=]\s*[\"']?"
    r"(CORRECTED_PREMISE|NOT_FOUND|PROVEN|SUPPORTED|UNKNOWN|UNVERIFIED)\b"
)
AUTHORITATIVE_TOOL_MARKERS = (
    "github",
    "gitlab",
    "bitbucket",
    "browser",
    "web",
    "mcp",
    "http",
    "url",
    "remote_api",
)
AUTHORITATIVE_ARG_MARKERS = (
    "github.com",
    "api.github.com",
    "gitlab.com",
    "bitbucket.org",
    "http://",
    "https://",
)


def unavailable_but_honest(content: str) -> bool:
    lowered = content.lower()
    return (
        "unverified" in lowered
        and any(
            token in lowered
            for token in (
                "unavailable",
                "could not invoke",
                "cannot invoke",
                "not available",
                "unable to invoke",
            )
        )
    )


def recorded_calls(payload: dict[str, Any]) -> list[tuple[int, str, str]]:
    state = load_state(payload, "evidence-events")
    raw_events = state.get("events") if isinstance(state.get("events"), list) else []
    result: list[tuple[int, str, str]] = []
    for fallback, event in enumerate(raw_events):
        if not isinstance(event, dict) or event.get("status") != "completed":
            continue
        try:
            order = int(event.get("step", fallback))
        except Exception:
            order = fallback
        name = str(event.get("name") or "")
        text = str(event.get("argsText") or "").lower()
        if name:
            result.append((order, name, text))
    result.sort(key=lambda item: item[0])
    return result


def transcript_fallback_calls(payload: dict[str, Any]) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    for order, name, args in tool_calls(payload):
        try:
            text = json.dumps(args, ensure_ascii=False, sort_keys=True).lower()
        except Exception:
            text = str(args).lower()
        result.append((order, name, text))
    return result


def final_conclusion(content: str) -> str:
    stripped = content.strip()
    if not stripped:
        return ""
    try:
        parsed = json.loads(stripped)
    except Exception:
        parsed = None
    if isinstance(parsed, dict):
        value = parsed.get("conclusion")
        if isinstance(value, str):
            return value.strip().upper()
    match = CONCLUSION_RE.search(content)
    return match.group(1).upper() if match else ""


def looks_like_current_external_state(content: str) -> bool:
    return bool(EXTERNAL_STATE_RE.search(content))


def has_authoritative_external_evidence(calls: list[tuple[int, str, str]]) -> bool:
    """Recognize direct platform/web evidence, never local Git/file inspection alone."""
    for _, name, args_text in calls:
        lowered_name = name.lower()
        if any(marker in lowered_name for marker in AUTHORITATIVE_TOOL_MARKERS):
            return True
        if any(marker in args_text for marker in AUTHORITATIVE_ARG_MARKERS):
            return True
    return False


def external_state_final_gate(
    payload: dict[str, Any],
    calls: list[tuple[int, str, str]],
    latest: str,
) -> str | None:
    """Return a blocking reason when the final external-state verdict outruns evidence.

    This check intentionally runs for read-only tasks too. Local list/read/Git evidence can support
    local sub-claims, but cannot justify a proposition-level verdict about a current external object.
    """
    conclusion = final_conclusion(latest)
    if conclusion not in STRONG_EXTERNAL_VERDICTS:
        save_state(payload, "external-state-final-gate", {"signature": "clear", "attempts": 0})
        return None
    if not looks_like_current_external_state(latest):
        return None
    if has_authoritative_external_evidence(calls):
        save_state(payload, "external-state-final-gate", {"signature": "clear", "attempts": 0})
        return None

    signature = conclusion
    state = load_state(payload, "external-state-final-gate")
    attempts = int(state.get("attempts", 0)) + 1 if state.get("signature") == signature else 1
    save_state(payload, "external-state-final-gate", {"signature": signature, "attempts": attempts})

    escalation = ""
    if attempts >= 2:
        escalation = (
            " This is the final structured-verdict gate, not optional guidance: rewrite the top-level "
            "conclusion before stopping."
        )
    return (
        "THALARCH EXTERNAL-STATE FINAL VERDICT GATE: completion is blocked because the final "
        f"conclusion is {conclusion}, but no authoritative current platform/service evidence was "
        "observed. For the main current external-state proposition, UNKNOWN/UNVERIFIED takes "
        "precedence and verdict selection stops there. Local absence of remotes, metadata, files, "
        "or references may be reported only as local facts. Set the top-level conclusion to UNKNOWN "
        "or UNVERIFIED, explicitly name the missing authoritative proof, populate any unverified/unknown "
        "ledger, and do not use CORRECTED_PREMISE/NOT_FOUND/PROVEN/SUPPORTED until authoritative "
        "external evidence actually exists."
        + escalation
    )


def main() -> None:
    payload = read_payload()
    if not bool(payload.get("fullyIdle", True)):
        emit({"decision": "stop"})
        return

    reason = str(payload.get("terminationReason") or "").lower()
    if reason in {
        "error",
        "max_steps_exceeded",
        "cancelled",
        "canceled",
        "user_cancelled",
        "user_canceled",
    }:
        emit({"decision": "stop"})
        return

    calls = recorded_calls(payload)
    if not calls:
        calls = transcript_fallback_calls(payload)

    latest = latest_model_content(payload)
    external_block = external_state_final_gate(payload, calls, latest)
    if external_block:
        emit({"decision": "continue", "reason": external_block})
        return

    if not calls:
        emit({"decision": "stop"})
        return

    mutation_orders: list[int] = []
    visual_orders: list[int] = []
    web_orders: list[int] = []
    fact_orders: list[int] = []
    verifier_orders: list[int] = []
    vision_review_orders: list[int] = []
    design_review_orders: list[int] = []
    orchestrated_mutation = False

    for order, name, text in calls:
        lowered_name = name.lower()
        if lowered_name != "invoke_subagent":
            continue

        if any(agent in text for agent in MUTATOR_AGENTS):
            orchestrated_mutation = True
            mutation_orders.append(order)
        if "thalarch-visual-director" in text:
            visual_orders.append(order)
        if "thalarch-web-designer" in text:
            web_orders.append(order)
        if "thalarch-fact-checker" in text:
            fact_orders.append(order)
        if "thalarch-verifier" in text:
            verifier_orders.append(order)
        if "thalarch-vision-reviewer" in text:
            vision_review_orders.append(order)
        if "thalarch-design-reviewer" in text:
            design_review_orders.append(order)

    # Enforce the orchestration completion protocol only at the parent/orchestrator boundary.
    # Direct implementation subagents must be able to return evidence to their parent.
    if not orchestrated_mutation:
        emit({"decision": "stop"})
        return

    last_mutation = max(mutation_orders)
    missing: list[str] = []

    last_fact = max(fact_orders) if fact_orders else -1
    if last_fact <= last_mutation:
        missing.append("independent fact-check after the final mutation")

    last_vision = max(vision_review_orders) if vision_review_orders else -1
    if visual_orders and last_vision <= max(visual_orders):
        missing.append("independent vision review after the final generated/edited visual asset")

    last_design = max(design_review_orders) if design_review_orders else -1
    if web_orders and last_design <= max(web_orders):
        missing.append("independent design review after the final web-design implementation")

    required_before_verifier = max(last_mutation, last_fact, last_vision, last_design)
    last_verifier = max(verifier_orders) if verifier_orders else -1
    if last_verifier <= required_before_verifier:
        missing.append("cold verifier after all applicable fact/design/vision checks")

    if not missing:
        save_state(payload, "stop-evidence-gate", {"signature": "clear", "attempts": 0})
        emit({"decision": "stop"})
        return

    if unavailable_but_honest(latest):
        # Honest incompleteness is permitted; fabricated completion is not.
        emit({"decision": "stop"})
        return

    signature = f"{last_mutation}|{'|'.join(sorted(missing))}"
    state = load_state(payload, "stop-evidence-gate")
    attempts = int(state.get("attempts", 0)) + 1 if state.get("signature") == signature else 1
    save_state(payload, "stop-evidence-gate", {"signature": signature, "attempts": attempts})

    missing_text = "; ".join(missing)
    escalation = ""
    if attempts >= 3:
        escalation = (
            " If a required Thalarch specialist is genuinely unavailable, stop trying to satisfy "
            "the gate with prose: report exactly which proof could not be obtained and preserve "
            "that acceptance claim as UNVERIFIED."
        )

    emit({
        "decision": "continue",
        "reason": (
            "THALARCH HARD EVIDENCE GATE: completion is blocked because the final implementation "
            f"mutation is not followed by the required independent evidence: {missing_text}. "
            "Do not claim DONE, PASS, fixed, visually correct, pushed/published, or regression-free. "
            "Run the missing independent checks from current evidence, then cold-verify acceptance."
            + escalation
        ),
    })


if __name__ == "__main__":
    main()
