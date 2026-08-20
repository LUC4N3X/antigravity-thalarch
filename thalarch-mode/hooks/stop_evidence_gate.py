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
STRONG_VISUAL_VERDICTS = STRONG_EXTERNAL_VERDICTS
EXTERNAL_STATE_RE = re.compile(
    r"\b(?:pull\s+request|pr\b|issue\s+#?\d+|issue\s+url|"
    r"deploy(?:ment)?\s+(?:state|status|url|live)|"
    r"release\s+(?:state|status|url|live|published)|"
    r"publication\s+(?:state|status|url|live|published)|"
    r"remote\s+(?:state|object|url)|platform\s+url)\b|"
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/",
    re.IGNORECASE,
)
VISUAL_STATE_RE = re.compile(
    r"\b(?:looks?\s+(?:perfect|correct|right)|visually\s+(?:correct|verified|perfect)|"
    r"render(?:ed|ing)?\s+(?:correctly|perfectly|as\s+expected)|"
    r"visual\s+(?:state|fidelity|proof|verification)|"
    r"(?:mobile|desktop)\s+(?:layout|view|viewport|render|appearance)|"
    r"matches?\s+(?:the\s+)?(?:reference|design))\b",
    re.IGNORECASE,
)
VISUAL_UNVERIFIED_RE = re.compile(
    r"\b(?:render|browser|visual|screenshot|viewport|mobile|desktop|emulator|device)\w*\b",
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
VISUAL_EVIDENCE_TOOL_MARKERS = (
    "screenshot",
    "screen_capture",
    "capture_screen",
    "vision",
    "view_image",
    "image_view",
    "render",
    "emulator",
    "device",
    "playwright",
    "puppeteer",
    "viewport",
)
NON_EVIDENCE_TERMINAL_TOOLS = {"finish"}
USER_SOURCES = {"USER_EXPLICIT", "USER", "HUMAN"}
USER_TYPES = {"USER_INPUT", "REQUEST", "USER_MESSAGE", "HUMAN_MESSAGE"}
TRACE_ENV = "THALARCH_HOOK_TRACE_FILE"


def trace_event(event: str, **fields: Any) -> None:
    """Append opt-in diagnostic data without changing hook behavior."""
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
    """Return the newest terminal finish payload captured in the internal transcript."""
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
    """Return the latest explicit user request from Antigravity's transcript."""
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


def _walk_json(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def final_unverified_items(content: str) -> tuple[bool, list[str]]:
    """Return whether a structured unverified ledger exists and its string entries."""
    try:
        parsed = json.loads(content.strip())
    except Exception:
        return False, []
    for obj in _walk_json(parsed):
        if not isinstance(obj, dict) or "unverified" not in obj:
            continue
        raw = obj.get("unverified")
        if isinstance(raw, list):
            return True, [item for item in raw if isinstance(item, str)]
        return True, []
    return False, []


def looks_like_current_external_state(user_request: str, final_content: str) -> bool:
    """Classify the proposition from user intent plus the final answer, not answer wording alone."""
    combined = "\n".join(part for part in (user_request, final_content) if part)
    return bool(EXTERNAL_STATE_RE.search(combined))


def looks_like_visual_state(user_request: str, final_content: str) -> bool:
    """Recognize propositions whose truth depends on rendered/observed visual state."""
    combined = "\n".join(part for part in (user_request, final_content) if part)
    return bool(VISUAL_STATE_RE.search(combined))


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


def has_rendered_visual_evidence(calls: list[tuple[int, str, str]]) -> bool:
    """Require a tool capable of exposing rendered pixels/device visual state, not source inspection."""
    for _, name, _ in calls:
        lowered_name = name.lower()
        if lowered_name in NON_EVIDENCE_TERMINAL_TOOLS or lowered_name == "generate_image":
            continue
        if any(marker in lowered_name for marker in VISUAL_EVIDENCE_TOOL_MARKERS):
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


def visual_state_final_gate(
    payload: dict[str, Any],
    calls: list[tuple[int, str, str]],
    user_request: str,
    final_content: str,
) -> str | None:
    """Block visual-state verdicts that rely on source inspection instead of rendered evidence."""
    if not looks_like_visual_state(user_request, final_content):
        return None
    if has_rendered_visual_evidence(calls):
        save_state(payload, "visual-state-final-gate", {"signature": "clear", "attempts": 0})
        return None

    conclusion = final_conclusion(final_content)
    ledger_present, unverified_items = final_unverified_items(final_content)
    has_visual_reason = any(VISUAL_UNVERIFIED_RE.search(item) for item in unverified_items)
    if conclusion in {"UNKNOWN", "UNVERIFIED"} and (not ledger_present or has_visual_reason):
        save_state(payload, "visual-state-final-gate", {"signature": "clear", "attempts": 0})
        return None

    if conclusion not in STRONG_VISUAL_VERDICTS and conclusion not in {"UNKNOWN", "UNVERIFIED"}:
        return None

    signature = f"{conclusion}|{user_request[:160]}|{int(ledger_present)}|{int(has_visual_reason)}"
    state = load_state(payload, "visual-state-final-gate")
    attempts = int(state.get("attempts", 0)) + 1 if state.get("signature") == signature else 1
    save_state(payload, "visual-state-final-gate", {"signature": signature, "attempts": attempts})

    ledger_instruction = ""
    if ledger_present and not has_visual_reason:
        ledger_instruction = (
            " The structured output exposes an unverified ledger, so add a concrete missing visual proof "
            "there using terms such as render, browser, screenshot, viewport, mobile, or desktop."
        )
    escalation = ""
    if attempts >= 2:
        escalation = " Rewrite the structured verdict/ledger before stopping; source inspection is not visual proof."

    return (
        "THALARCH VISUAL-STATE FINAL VERDICT GATE: completion is blocked because the user's main "
        "proposition depends on rendered visual state, but no rendered/browser/screenshot/device evidence "
        "was observed. Source code, CSS, DOM text, or a generation prompt cannot prove how the page actually "
        "looks on mobile or desktop. UNKNOWN/UNVERIFIED takes precedence and verdict selection stops there. "
        "Set the top-level conclusion to UNKNOWN or UNVERIFIED and explicitly name the missing visual proof. "
        "Do not use CORRECTED_PREMISE/NOT_FOUND/PROVEN/SUPPORTED for the main visual proposition until "
        "appropriate rendered evidence actually exists."
        + ledger_instruction
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
    is_visual = looks_like_visual_state(user_request, final_content)
    rendered_visual_evidence = has_rendered_visual_evidence(calls)
    trace_event(
        "stop_observation",
        conclusion=conclusion,
        current_external_state=is_external,
        authoritative_external_evidence=authoritative,
        visual_state=is_visual,
        rendered_visual_evidence=rendered_visual_evidence,
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

    visual_block = visual_state_final_gate(payload, calls, user_request, final_content)
    if visual_block:
        emit_decision(
            "continue",
            reason=visual_block,
            gate="visual_state_final_gate",
            conclusion=conclusion,
            visual_state=is_visual,
            rendered_visual_evidence=rendered_visual_evidence,
        )
        return

    if not calls:
        emit_decision(
            "stop",
            reason="no_observed_calls",
            conclusion=conclusion,
            current_external_state=is_external,
            authoritative_external_evidence=authoritative,
            visual_state=is_visual,
            rendered_visual_evidence=rendered_visual_evidence,
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
