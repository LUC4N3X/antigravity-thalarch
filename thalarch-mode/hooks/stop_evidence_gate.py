#!/usr/bin/env python3
"""Prevent final output from outrunning the evidence actually observed.

Primary evidence comes from the hook event ledger written by PreToolUse/PostToolUse.
Transcript parsing is retained both for final-answer epistemic checks and as a
backward-compatible source of user intent/tool evidence.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from hook_utils import (
    emit,
    latest_model_content,
    load_state,
    read_payload,
    save_state,
    tool_calls,
    transcript_steps,
)

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
    r"\b(?:pull\s+request|pr\b|issue\s+#?\d+|issue\s+url|"
    r"deploy(?:ment)?\s+(?:state|status|url|live)|"
    r"release\s+(?:state|status|url|live|published)|"
    r"publication\s+(?:state|status|url|live|published)|"
    r"remote\s+(?:state|object|url)|platform\s+url)\b|"
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/",
    re.IGNORECASE,
)
CONCLUSION_RE = re.compile(
    r"[\"']?conclusion[\"']?\s*[:=]\s*[\"']?"
    r"(CORRECTED_PREMISE|NOT_FOUND|PROVEN|SUPPORTED|UNKNOWN|UNVERIFIED)\b",
    re.IGNORECASE,
)
AUTHORITATIVE_TOOL_MARKERS = (
    "github",
    "gitlab",
    "bitbucket",
    "search_web",
    "browser",
    "web",
    "mcp",
    "http",
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
NON_EVIDENCE_TERMINAL_TOOLS = {"finish"}
USER_SOURCES = {"USER_EXPLICIT", "USER", "HUMAN"}
USER_TYPES = {"USER_INPUT", "REQUEST", "USER_MESSAGE", "HUMAN_MESSAGE"}
TRACE_ENV = "THALARCH_HOOK_TRACE_FILE"


def trace_event(event: str, **fields: Any) -> None:
    """Append opt-in diagnostic data without changing hook behavior.

    The trace is disabled unless THALARCH_HOOK_TRACE_FILE is explicitly set by a
    benchmark/debug shell. This keeps normal Thalarch operation side-effect free.
    """
    raw = os.environ.get(TRACE_ENV, "").strip()
    if not raw:
        return
    try:
        path = Path(raw).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"event": event, **fields}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        # Diagnostics must never change the epistemic decision or break completion.
        pass


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


def observed_calls(payload: dict[str, Any]) -> list[tuple[int, str, str]]:
    """Merge event-ledger and transcript calls without discarding either evidence source."""
    merged = recorded_calls(payload) + transcript_fallback_calls(payload)
    seen: set[tuple[int, str, str]] = set()
    result: list[tuple[int, str, str]] = []
    for item in sorted(merged, key=lambda value: value[0]):
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def finish_payload_text(calls: list[tuple[int, str, str]]) -> str:
    """Return the newest terminal finish payload captured in the internal transcript.

    Antigravity CLI can invoke Stop before the final planner response is materialized in
    transcript content. The finish tool arguments are already present at that point and
    therefore provide the last pre-delivery representation of the structured answer.
    """
    finish_calls = [(order, text) for order, name, text in calls if name.lower() == "finish"]
    return max(finish_calls, key=lambda item: item[0])[1] if finish_calls else ""


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


def latest_user_request(payload: dict[str, Any]) -> str:
    """Return the latest explicit user request from Antigravity's transcript.

    Current Antigravity transcripts use USER_EXPLICIT/USER_INPUT, while older or
    alternate builds may use USER/REQUEST-style names. Provider-added metadata is
    excluded when the request is wrapped in <USER_REQUEST> tags.
    """
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
        if request:
            try:
                order = int(step.get("step_index", step.get("stepIndex", fallback)))
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


def looks_like_current_external_state(user_request: str, final_content: str) -> bool:
    """Classify the proposition from user intent plus the final answer, not answer wording alone."""
    combined = "\n".join(part for part in (user_request, final_content) if part)
    return bool(EXTERNAL_STATE_RE.search(combined))


def has_authoritative_external_evidence(calls: list[tuple[int, str, str]]) -> bool:
    """Recognize direct platform/web evidence, never local Git/file/final-answer content alone."""
    for _, name, args_text in calls:
        lowered_name = name.lower()
        if lowered_name in NON_EVIDENCE_TERMINAL_TOOLS:
            continue
        if any(marker in lowered_name for marker in AUTHORITATIVE_TOOL_MARKERS):
            return True
        if any(marker in args_text for marker in AUTHORITATIVE_ARG_MARKERS):
            return True
    return False


def external_state_final_gate(
    payload: dict[str, Any],
    calls: list[tuple[int, str, str]],
    user_request: str,
    final_content: str,
) -> str | None:
    """Return a blocking reason when the final external-state verdict outruns evidence."""
    conclusion = final_conclusion(final_content)
    if conclusion not in STRONG_EXTERNAL_VERDICTS:
        save_state(payload, "external-state-final-gate", {"signature": "clear", "attempts": 0})
        return None
    if not looks_like_current_external_state(user_request, final_content):
        return None
    if has_authoritative_external_evidence(calls):
        save_state(payload, "external-state-final-gate", {"signature": "clear", "attempts": 0})
        return None

    signature = f"{conclusion}|{user_request[:160]}"
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
        "observed for the user's external-state request. For the main current external-state "
        "proposition, UNKNOWN/UNVERIFIED takes precedence and verdict selection stops there. Local "
        "absence of remotes, metadata, files, or references may be reported only as local facts. "
        "Set the top-level conclusion to UNKNOWN or UNVERIFIED, explicitly name the missing "
        "authoritative proof, populate any unverified/unknown ledger, and do not use "
        "CORRECTED_PREMISE/NOT_FOUND/PROVEN/SUPPORTED until authoritative external evidence actually exists."
        + escalation
    )


def emit_decision(decision: str, *, reason: str = "", **trace_fields: Any) -> None:
    trace_event("stop_decision", decision=decision, reason=reason[:240], **trace_fields)
    payload: dict[str, Any] = {"decision": decision}
    if reason:
        payload["reason"] = reason
    emit(payload)


def main() -> None:
    payload = read_payload()
    trace_event(
        "stop_enter",
        fully_idle=bool(payload.get("fullyIdle", True)),
        termination_reason=str(payload.get("terminationReason") or ""),
        transcript_path=str(payload.get("transcriptPath") or ""),
        payload_keys=sorted(str(key) for key in payload.keys()),
    )

    if not bool(payload.get("fullyIdle", True)):
        emit_decision("stop", reason="not_fully_idle")
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
        emit_decision("stop", reason=f"terminal_reason:{reason}")
        return

    calls = observed_calls(payload)
    latest = latest_model_content(payload)
    finish_text = finish_payload_text(calls)
    final_content = latest or finish_text
    user_request = latest_user_request(payload)
    conclusion = final_conclusion(final_content)
    is_external = looks_like_current_external_state(user_request, final_content)
    authoritative = has_authoritative_external_evidence(calls)
    trace_event(
        "stop_observation",
        conclusion=conclusion,
        current_external_state=is_external,
        authoritative_external_evidence=authoritative,
        final_content_source="model_content" if latest else ("finish_payload" if finish_text else "none"),
        observed_call_count=len(calls),
        observed_call_names=[name for _, name, _ in calls],
        finish_payload=finish_text[:2000],
        user_request=user_request[:500],
        latest_model_content=latest[:1000],
    )

    external_block = external_state_final_gate(payload, calls, user_request, final_content)
    if external_block:
        emit_decision(
            "continue",
            reason=external_block,
            gate="external_state_final_gate",
            conclusion=conclusion,
            current_external_state=is_external,
            authoritative_external_evidence=authoritative,
        )
        return

    if not calls:
        emit_decision(
            "stop",
            reason="no_observed_calls",
            conclusion=conclusion,
            current_external_state=is_external,
            authoritative_external_evidence=authoritative,
        )
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

    if not orchestrated_mutation:
        emit_decision("stop", reason="no_orchestrated_mutation")
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
        emit_decision("stop", reason="orchestration_evidence_complete")
        return

    if unavailable_but_honest(final_content):
        emit_decision("stop", reason="honest_unverified_escape")
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

    block_reason = (
        "THALARCH HARD EVIDENCE GATE: completion is blocked because the final implementation "
        f"mutation is not followed by the required independent evidence: {missing_text}. "
        "Do not claim DONE, PASS, fixed, visually correct, pushed/published, or regression-free. "
        "Run the missing independent checks from current evidence, then cold-verify acceptance."
        + escalation
    )
    emit_decision("continue", reason=block_reason, gate="orchestrated_stop_evidence_gate")


if __name__ == "__main__":
    main()
