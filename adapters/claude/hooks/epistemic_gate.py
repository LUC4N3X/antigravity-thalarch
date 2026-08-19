#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path


def payload() -> dict:
    try:
        return json.load(__import__("sys").stdin)
    except Exception:
        return {}


def emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def empty_state() -> dict:
    return {
        "seq": 0,
        "last_mutation": 0,
        "last_verification_attempt": 0,
        "last_verification_success": 0,
        "subagents": 0,
    }


def state_file(data: dict) -> Path:
    sid = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(data.get("session_id") or "unknown"))
    root = Path(tempfile.gettempdir()) / "thalarch-claude"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{sid}.json"


def load(data: dict) -> dict:
    p = state_file(data)
    if not p.exists():
        return empty_state()
    try:
        state = json.loads(p.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else empty_state()
    except Exception:
        return empty_state()


def save(data: dict, state: dict) -> None:
    state_file(data).write_text(json.dumps(state, indent=2), encoding="utf-8")


def advance(state: dict) -> int:
    state["seq"] = int(state.get("seq", 0)) + 1
    return state["seq"]


def command(data: dict) -> str:
    inp = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    return str(inp.get("command") or "").strip()


def deny(reason: str) -> None:
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def nearest_package(cwd: Path) -> tuple[Path | None, set[str]]:
    current = cwd
    for _ in range(8):
        package = current / "package.json"
        if package.is_file():
            try:
                raw = json.loads(package.read_text(encoding="utf-8"))
                scripts = raw.get("scripts") if isinstance(raw, dict) else {}
                return package, set(scripts) if isinstance(scripts, dict) else set()
            except Exception:
                return package, set()
        if current.parent == current:
            break
        current = current.parent
    return None, set()


def looks_like_verification(cmd: str) -> bool:
    c = cmd.lower()
    patterns = [
        r"(?:^|\s)(?:pytest|py\.test)(?:\s|$)",
        r"python(?:3)?\s+-m\s+(?:pytest|unittest)\b",
        r"\b(?:test|tests|check|checks|lint|typecheck|type-check|build|compile|verify|validate)\b",
        r"\bcargo\s+(?:test|check|clippy)\b",
        r"\bgo\s+test\b",
        r"\bmvnw?(?:\.cmd)?\b[^\n]*(?:\btest\b|\bverify\b|\bpackage\b|\bcompile\b)",
        r"\bgradlew?(?:\.bat)?\b[^\n]*(?:\btest\b|\bcheck\b|\bbuild\b|\bassemble\b|\bcompile\w*\b|\blint\b)",
    ]
    return any(re.search(pattern, c, re.I) for pattern in patterns)


def pretool(data: dict) -> None:
    tool = str(data.get("tool_name") or "")
    if tool not in {"Bash", "PowerShell"}:
        return

    cmd = command(data)
    cwd = Path(str(data.get("cwd") or os.getcwd())).expanduser()
    if not cwd.is_dir():
        deny(f"Thalarch: working directory does not exist: {cwd}")
        return

    if re.match(r"^(?:\./)?gradlew(?:\.bat)?\b", cmd, re.I) and not ((cwd / "gradlew").exists() or (cwd / "gradlew.bat").exists()):
        deny("Thalarch: Gradle wrapper was guessed but does not exist here. Discover the real build tool first.")
        return

    npm = re.match(r"^npm\s+run\s+([^\s;&|]+)", cmd, re.I)
    if npm:
        name = npm.group(1).strip("\"'")
        package, scripts = nearest_package(cwd)
        if package is None or name not in scripts:
            deny(f"Thalarch: npm script '{name}' is not declared by the nearest package.json. Inspect project scripts first.")
            return

    py = re.match(r"^(?:python3?|py(?:\s+-3)?)\s+(?!-m\b)(?:-u\s+)?[\"']?([^\"'\s;&|]+\.py)", cmd, re.I)
    if py and not (cwd / py.group(1)).resolve().is_file():
        deny(f"Thalarch: Python script does not exist: {py.group(1)}")
        return


def posttool(data: dict, succeeded: bool) -> None:
    state = load(data)
    tool = str(data.get("tool_name") or "")
    cmd = command(data)
    order = advance(state)

    mutated = succeeded and tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}
    verification_attempt = False

    if tool in {"Bash", "PowerShell"}:
        verification_attempt = looks_like_verification(cmd)
        if succeeded:
            mutated = mutated or bool(re.search(
                r"(?:^|[;&|])\s*(?:sed\s+-i|perl\s+-pi|tee\s+|cat\s+>|echo\s+.*>|rm\s+|mv\s+|cp\s+)",
                cmd,
                re.I,
            ))

    if mutated:
        state["last_mutation"] = order
    if verification_attempt:
        state["last_verification_attempt"] = order
        if succeeded:
            state["last_verification_success"] = order

    save(data, state)


def stop(data: dict) -> None:
    if bool(data.get("stop_hook_active")):
        return

    state = load(data)
    msg = str(data.get("last_assistant_message") or "")
    last_mutation = int(state.get("last_mutation", 0))
    last_attempt = int(state.get("last_verification_attempt", 0))
    last_success = int(state.get("last_verification_success", 0))

    needs_verification = last_mutation > 0
    success_after_mutation = last_success > last_mutation
    no_later_failed_attempt = last_attempt == 0 or last_success >= last_attempt
    evidence_is_current = (not needs_verification) or (success_after_mutation and no_later_failed_attempt)

    if not evidence_is_current and "unverified" not in msg.lower():
        emit({
            "decision": "block",
            "reason": (
                "THALARCH EVIDENCE GATE: the final code/repository mutation is not followed by a successful current project-native verification, "
                "or a later verification attempt failed. Run the strongest relevant test/build/check after the final mutation, resolve any later failure, "
                "or explicitly keep the affected completion claim UNVERIFIED."
            ),
        })


def main() -> None:
    data = payload()
    event = str(data.get("hook_event_name") or "")
    if event == "UserPromptSubmit":
        emit({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "Thalarch 1.0.0: verify cheap facts before asserting them; ground version-sensitive APIs; never invent paths, commands, "
                    "test/CI/publication results or visual state; use UNKNOWN/UNVERIFIED when evidence is missing; seek disconfirming evidence on difficult work."
                ),
            }
        })
    elif event == "PreToolUse":
        pretool(data)
    elif event == "PostToolUse":
        # Claude Code documents PostToolUse as the successful execution event.
        posttool(data, succeeded=True)
    elif event == "PostToolUseFailure":
        # A failed verification must invalidate any earlier success that the model might otherwise reuse.
        posttool(data, succeeded=False)
    elif event == "SubagentStop":
        state = load(data)
        state["subagents"] = int(state.get("subagents", 0)) + 1
        save(data, state)
    elif event == "Stop":
        stop(data)


if __name__ == "__main__":
    main()
