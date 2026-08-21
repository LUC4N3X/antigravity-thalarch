#!/usr/bin/env python3
"""Front-door Stop gate for fresh, modality-correct evidence.

This wrapper adds three guarantees before delegating to stop_evidence_gate.py:
1. final content and evidence are scoped to the latest explicit user request;
2. current external/visual claims cannot reuse evidence from an earlier user turn;
3. test/build/lint/typecheck/benchmark claims require a successful matching runtime event
   from the latest request, not a stale or merely attempted command.

The existing stop_evidence_gate remains the canonical external/visual/orchestration gate.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from hook_utils import emit, load_state, tool_calls, transcript_steps

HOOKS = Path(__file__).resolve().parent
LEGACY_GATE = HOOKS / "stop_evidence_gate.py"

STRONG_VERDICTS = {"CORRECTED_PREMISE", "NOT_FOUND", "PROVEN", "SUPPORTED"}
USER_SOURCES = {"USER_EXPLICIT", "USER", "HUMAN"}
USER_TYPES = {"USER_INPUT", "REQUEST", "USER_MESSAGE", "HUMAN_MESSAGE"}
NON_EVIDENCE_TERMINAL_TOOLS = {"finish"}

CONCLUSION_RE = re.compile(
    r"[\"']?conclusion[\"']?\s*[:=]\s*[\"']?"
    r"(CORRECTED_PREMISE|NOT_FOUND|PROVEN|SUPPORTED|UNKNOWN|UNVERIFIED)\b",
    re.IGNORECASE,
)
EXTERNAL_STATE_RE = re.compile(
    r"\b(?:pull\s+request|pr\b|issue\s+#?\d+|issue\s+url|"
    r"deploy(?:ment)?\s+(?:state|status|url|live)|"
    r"release\s+(?:state|status|url|live|published)|"
    r"publication\s+(?:state|status|url|live|published)|"
    r"remote\s+(?:state|object|url)|platform\s+url|"
    r"ci\s+(?:state|status|green|passing|failed)|"
    r"workflow\s+(?:run|status)|pipeline\s+(?:state|status)|check\s+(?:run|status))\b|"
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
RUNTIME_STATE_RE = re.compile(
    r"\b(?:"
    r"(?:all\s+)?tests?\b[^\n.!?]{0,80}\b(?:pass|passed|passing|succeed|succeeds|succeeded|green)|"
    r"(?:full|entire)\s+(?:test\s+)?suite\b[^\n.!?]{0,80}\b(?:pass|passed|passing|succeed|succeeds|succeeded|green)|"
    r"(?:build|compile|compilation)\b[^\n.!?]{0,80}\b(?:pass|passes|passed|succeed|succeeds|succeeded|successful)|"
    r"(?:lint|linter|typecheck|type-check|type\s+check)\b[^\n.!?]{0,80}\b(?:pass|passes|passed|clean|succeed|succeeds|succeeded)|"
    r"benchmark\b[^\n.!?]{0,80}\b(?:pass|passes|passed|completed|completes|succeed|succeeds|succeeded)|"
    r"(?:command|script|job)\b[^\n.!?]{0,80}\b(?:pass|passes|passed|work|works|succeed|succeeds|succeeded)"
    r")\b",
    re.IGNORECASE,
)
RUNTIME_NEGATION_RE = re.compile(
    r"\b(?:cannot|can't|couldn't|could\s+not|didn't|did\s+not|not\s+run|not\s+executed|"
    r"unverified|unknown|unable\s+to|without\s+(?:running|executing))\b",
    re.IGNORECASE,
)
RUNTIME_QUESTION_CONTEXT_RE = re.compile(
    r"\b(?:whether|do|does|did|can|could|would|will|confirm\s+if|tell\s+me\s+if)\b",
    re.IGNORECASE,
)
RUNTIME_UNVERIFIED_RE = re.compile(
    r"\b(?:test|suite|run|execut|build|compile|lint|typecheck|type-check|benchmark|command|runtime)\w*\b",
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
RUNTIME_TOOL_MARKERS = ("run_command", "shell", "bash", "powershell", "terminal", "exec")

TEST_COMMAND_RE = re.compile(
    r"\b(?:pytest|unittest|jest|vitest|ctest|go\s+test|cargo\s+test|mvn(?:w)?\b[^\n]*\btest|"
    r"gradle(?:w)?\b[^\n]*\btest|npm\b[^\n]*\btest|pnpm\b[^\n]*\btest|yarn\b[^\n]*\btest)\b",
    re.IGNORECASE,
)
BUILD_COMMAND_RE = re.compile(
    r"\b(?:gradle(?:w)?\b[^\n]*\b(?:build|assemble|compile)|mvn(?:w)?\b[^\n]*\b(?:package|verify|compile)|"
    r"cargo\s+build|go\s+build|npm\b[^\n]*\bbuild|pnpm\b[^\n]*\bbuild|yarn\b[^\n]*\bbuild|"
    r"tsc\b|dotnet\s+build|cmake\b[^\n]*--build)\b",
    re.IGNORECASE,
)
LINT_COMMAND_RE = re.compile(
    r"\b(?:lint|eslint|ruff|flake8|pylint|ktlint|detekt|clippy)\b",
    re.IGNORECASE,
)
TYPECHECK_COMMAND_RE = re.compile(
    r"\b(?:typecheck|type-check|mypy|pyright|tsc\b[^\n]*(?:--noemit|--noEmit)|cargo\s+check)\b",
    re.IGNORECASE,
)
BENCH_COMMAND_RE = re.compile(r"\b(?:bench|benchmark|hyperfine|criterion|pytest-benchmark)\b", re.IGNORECASE)


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


def _step_order(step: dict[str, Any], fallback: int) -> int:
    raw = step.get("step_index", step.get("stepIndex", step.get("_thalarch_line_index", fallback)))
    try:
        return int(raw)
    except Exception:
        return fallback


def latest_user_context(payload: dict[str, Any]) -> tuple[int, str, str]:
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
            candidates.append((_step_order(step, fallback), request))

    if candidates:
        order, request = max(candidates, key=lambda item: item[0])
    else:
        order, request = -1, ""
        for key in ("userPrompt", "userMessage", "prompt", "request"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                request = _extract_user_request(value)
                break

    request_key = hashlib.sha256(request.encode("utf-8")).hexdigest()[:16] if request else ""
    return order, request, request_key


def current_model_content(payload: dict[str, Any], user_order: int) -> str:
    """Return only model content produced after the latest explicit user request."""
    candidates: list[tuple[int, str]] = []
    for fallback, step in enumerate(transcript_steps(payload)):
        order = _step_order(step, fallback)
        if user_order >= 0 and order <= user_order:
            continue
        source = str(step.get("source") or "").upper()
        status = str(step.get("status") or "").upper()
        typ = str(step.get("type") or "").upper()
        content = step.get("content")
        if source == "MODEL" and status in ("", "DONE") and typ == "PLANNER_RESPONSE" and isinstance(content, str):
            candidates.append((order, content))
    return max(candidates, key=lambda item: item[0])[1] if candidates else ""


def transcript_call_rows(payload: dict[str, Any]) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    for order, name, args in tool_calls(payload):
        try:
            text = json.dumps(args, ensure_ascii=False, sort_keys=True).lower()
        except Exception:
            text = str(args).lower()
        rows.append((order, name, text))
    rows.sort(key=lambda item: item[0])
    return rows


def finish_payload_text(calls: list[tuple[int, str, str]]) -> str:
    finish_calls = [(order, text) for order, name, text in calls if name.lower() == "finish"]
    return max(finish_calls, key=lambda item: item[0])[1] if finish_calls else ""


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


def final_unverified_items(content: str) -> tuple[bool, list[str]]:
    try:
        parsed = json.loads(content.strip())
    except Exception:
        return False, []
    if not isinstance(parsed, dict) or "unverified" not in parsed:
        return False, []
    raw = parsed.get("unverified")
    if isinstance(raw, list):
        return True, [item for item in raw if isinstance(item, str)]
    return True, []


def is_authoritative_external_call(name: str, args_text: str) -> bool:
    lowered = name.lower()
    if lowered in NON_EVIDENCE_TERMINAL_TOOLS:
        return False
    return any(marker in lowered for marker in AUTHORITATIVE_TOOL_MARKERS) or any(
        marker in args_text for marker in AUTHORITATIVE_ARG_MARKERS
    )


def is_visual_evidence_call(name: str) -> bool:
    lowered = name.lower()
    if lowered in NON_EVIDENCE_TERMINAL_TOOLS or lowered == "generate_image":
        return False
    return any(marker in lowered for marker in VISUAL_EVIDENCE_TOOL_MARKERS)


def runtime_kind(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(?:test|tests|suite)\b", lowered):
        return "test"
    if re.search(r"\b(?:build|compile|compilation)\b", lowered):
        return "build"
    if re.search(r"\b(?:lint|linter)\b", lowered):
        return "lint"
    if re.search(r"\b(?:typecheck|type-check|type\s+check)\b", lowered):
        return "typecheck"
    if re.search(r"\bbenchmark\b", lowered):
        return "benchmark"
    return "command"


def runtime_command_matches(kind: str, args_text: str) -> bool:
    if kind == "test":
        return bool(TEST_COMMAND_RE.search(args_text))
    if kind == "build":
        return bool(BUILD_COMMAND_RE.search(args_text))
    if kind == "lint":
        return bool(LINT_COMMAND_RE.search(args_text))
    if kind == "typecheck":
        return bool(TYPECHECK_COMMAND_RE.search(args_text))
    if kind == "benchmark":
        return bool(BENCH_COMMAND_RE.search(args_text))
    return any(marker in args_text for marker in ("run", "exec", "script", "job"))


def successful_runtime_evidence(payload: dict[str, Any], request_key: str, kind: str) -> bool:
    if not request_key:
        return False
    state = load_state(payload, "evidence-events")
    events = state.get("events") if isinstance(state.get("events"), list) else []
    for event in events:
        if not isinstance(event, dict) or event.get("status") != "completed":
            continue
        if str(event.get("requestKey") or "") != request_key:
            continue
        name = str(event.get("name") or "").lower()
        if not any(marker in name for marker in RUNTIME_TOOL_MARKERS):
            continue
        args_text = str(event.get("argsText") or "").lower()
        if runtime_command_matches(kind, args_text):
            return True
    return False


def assertive_runtime_prose(content: str) -> bool:
    for match in RUNTIME_STATE_RE.finditer(content):
        prefix = content[max(0, match.start() - 100) : match.start()]
        if RUNTIME_NEGATION_RE.search(prefix) or RUNTIME_QUESTION_CONTEXT_RE.search(prefix):
            continue
        return True
    return False


def block_reason(kind: str, detail: str) -> str:
    return (
        "THALARCH FRESH PROOF GATE: completion is blocked because a "
        f"{kind} claim outruns current-request evidence. {detail} "
        "Evidence from an earlier user turn, a failed/attempted command, source inspection, or model confidence "
        "does not count as fresh proof. Use UNKNOWN/UNVERIFIED for the main proposition until the correct proof "
        "is successfully observed in the current request, and name the missing proof in any structured unverified ledger."
    )


def delegate_legacy(raw_payload: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(LEGACY_GATE)],
        input=raw_payload,
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        print(proc.stdout.strip())
        return
    emit({
        "decision": "continue",
        "reason": (
            "THALARCH FRESH PROOF GATE: the canonical completion verifier could not run successfully. "
            "Do not claim verified completion; preserve acceptance as UNVERIFIED until the Stop verifier succeeds."
        ),
    })


def main() -> None:
    raw_payload = sys.stdin.read()
    try:
        parsed = json.loads(raw_payload)
        payload = parsed if isinstance(parsed, dict) else {}
    except Exception:
        payload = {}

    # Terminal infrastructure/cancellation states are not epistemic retries.
    reason = str(payload.get("terminationReason") or "").lower()
    if reason in {
        "error",
        "max_steps_exceeded",
        "cancelled",
        "canceled",
        "user_cancelled",
        "user_canceled",
    }:
        delegate_legacy(raw_payload)
        return

    user_order, user_request, request_key = latest_user_context(payload)
    all_calls = transcript_call_rows(payload)
    current_calls = [row for row in all_calls if user_order < 0 or row[0] > user_order]
    latest = current_model_content(payload, user_order)
    final_content = latest or finish_payload_text(current_calls) or finish_payload_text(all_calls)
    conclusion = final_conclusion(final_content)
    combined = "\n".join(part for part in (user_request, final_content) if part)

    is_external = bool(EXTERNAL_STATE_RE.search(combined))
    is_visual = bool(VISUAL_STATE_RE.search(combined))
    is_runtime = bool(RUNTIME_STATE_RE.search(combined))

    if conclusion in STRONG_VERDICTS and is_external:
        current_external = any(is_authoritative_external_call(name, args) for _, name, args in current_calls)
        if not current_external:
            emit({
                "decision": "continue",
                "reason": block_reason(
                    "current external-state",
                    "No authoritative platform/service evidence was observed after the latest user request.",
                ),
            })
            return

    if conclusion in STRONG_VERDICTS and is_visual:
        current_visual = any(is_visual_evidence_call(name) for _, name, _ in current_calls)
        if not current_visual:
            emit({
                "decision": "continue",
                "reason": block_reason(
                    "rendered visual-state",
                    "No browser/screenshot/device/render evidence was observed after the latest user request.",
                ),
            })
            return

    if is_runtime:
        strong_runtime = conclusion in STRONG_VERDICTS or assertive_runtime_prose(final_content)
        kind = runtime_kind(combined)
        if strong_runtime and not successful_runtime_evidence(payload, request_key, kind):
            emit({
                "decision": "continue",
                "reason": block_reason(
                    f"runtime {kind}",
                    "No successful matching execution event is recorded for the latest user request.",
                ),
            })
            return

        ledger_present, items = final_unverified_items(final_content)
        if conclusion in {"UNKNOWN", "UNVERIFIED"} and ledger_present:
            has_runtime_reason = any(RUNTIME_UNVERIFIED_RE.search(item) for item in items)
            if not has_runtime_reason:
                emit({
                    "decision": "continue",
                    "reason": block_reason(
                        f"runtime {kind}",
                        "The structured unverified ledger exists but does not name the missing runtime proof.",
                    ),
                })
                return

    delegate_legacy(raw_payload)


if __name__ == "__main__":
    main()
