#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path


def read_input() -> dict:
    try:
        return json.load(__import__("sys").stdin)
    except Exception:
        return {}


def emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def empty_state() -> dict:
    return {"seq": 0, "last_mutation": 0, "last_verification": 0, "subagents": 0}


def state_path(payload: dict) -> Path:
    session = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(payload.get("session_id") or "unknown"))
    root = Path(tempfile.gettempdir()) / "thalarch-codex"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{session}.json"


def load_state(payload: dict) -> dict:
    path = state_path(payload)
    if not path.exists():
        return empty_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else empty_state()
    except Exception:
        return empty_state()


def save_state(payload: dict, state: dict) -> None:
    state_path(payload).write_text(json.dumps(state, indent=2), encoding="utf-8")


def advance(state: dict) -> int:
    state["seq"] = int(state.get("seq", 0)) + 1
    return state["seq"]


def deny(reason: str) -> None:
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def bash_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    return str(tool_input.get("command") or "").strip()


def package_scripts(cwd: Path) -> tuple[Path | None, set[str]]:
    current = cwd
    for _ in range(8):
        candidate = current / "package.json"
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                scripts = data.get("scripts") if isinstance(data, dict) else {}
                return candidate, set(scripts) if isinstance(scripts, dict) else set()
            except Exception:
                return candidate, set()
        if current.parent == current:
            break
        current = current.parent
    return None, set()


def pretool(payload: dict) -> None:
    if str(payload.get("tool_name") or "") != "Bash":
        emit({})
        return
    command = bash_command(payload)
    cwd = Path(str(payload.get("cwd") or os.getcwd())).expanduser()
    if not cwd.is_dir():
        deny(f"Thalarch: working directory does not exist: {cwd}")
        return

    if re.match(r"^(?:\./)?gradlew(?:\.bat)?\b", command, re.I):
        if not ((cwd / "gradlew").exists() or (cwd / "gradlew.bat").exists()):
            deny("Thalarch: Gradle wrapper command was guessed but no gradlew/gradlew.bat exists in the current project directory.")
            return

    npm = re.match(r"^npm\s+run\s+([^\s;&|]+)", command, re.I)
    if npm:
        script = npm.group(1).strip("\"'")
        package, scripts = package_scripts(cwd)
        if package is None or script not in scripts:
            deny(f"Thalarch: npm script '{script}' is not declared by the nearest package.json. Inspect project scripts before running it.")
            return

    py = re.match(r"^(?:python3?|py(?:\s+-3)?)\s+(?!-m\b)(?:-u\s+)?[\"']?([^\"'\s;&|]+\.py)", command, re.I)
    if py:
        target = (cwd / py.group(1)).resolve()
        if not target.is_file():
            deny(f"Thalarch: Python script does not exist: {py.group(1)}")
            return

    emit({})


def posttool(payload: dict) -> None:
    state = load_state(payload)
    tool = str(payload.get("tool_name") or "")
    command = bash_command(payload)
    order = advance(state)

    mutated = tool == "apply_patch"
    verified = False

    if tool == "Bash":
        verified = bool(re.search(
            r"\b(test|check|lint|typecheck|build|compile|verify|pytest|unittest|gradle|mvn|cargo\s+test|go\s+test)\b",
            command,
            re.I,
        ))
        mutated = mutated or bool(re.search(
            r"(?:^|[;&|])\s*(?:sed\s+-i|perl\s+-pi|tee\s+|cat\s+>|echo\s+.*>|rm\s+|mv\s+|cp\s+)",
            command,
            re.I,
        ))

    if mutated:
        state["last_mutation"] = order
    if verified:
        state["last_verification"] = order

    save_state(payload, state)
    emit({})


def subagent_stop(payload: dict) -> None:
    state = load_state(payload)
    state["subagents"] = int(state.get("subagents", 0)) + 1
    save_state(payload, state)
    emit({})


def stop(payload: dict) -> None:
    if bool(payload.get("stop_hook_active")):
        emit({})
        return

    state = load_state(payload)
    message = str(payload.get("last_assistant_message") or "")
    last_mutation = int(state.get("last_mutation", 0))
    last_verification = int(state.get("last_verification", 0))

    verification_is_fresh = last_mutation == 0 or last_verification > last_mutation
    if not verification_is_fresh and "unverified" not in message.lower():
        emit({
            "decision": "block",
            "reason": (
                "THALARCH EVIDENCE GATE: the latest repository mutation is newer than the latest observed test/build/check evidence. "
                "Run the strongest project-native verification available after the final mutation, or explicitly report the affected completion claims as UNVERIFIED."
            ),
        })
        return
    emit({})


def prompt(payload: dict) -> None:
    emit({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "Thalarch 1.0.0 reliability contract: inspect cheap facts before asserting them; verify version-sensitive APIs against the actual project version and primary docs; "
                "never invent paths, symbols, commands, test results, CI/publication state, benchmark numbers, or visual state; use UNKNOWN/UNVERIFIED when evidence is missing; "
                "for difficult work seek disconfirming evidence and independent review before claiming completion."
            ),
        }
    })


def main() -> None:
    payload = read_input()
    event = str(payload.get("hook_event_name") or "")
    if event == "UserPromptSubmit":
        prompt(payload)
    elif event == "PreToolUse":
        pretool(payload)
    elif event == "PostToolUse":
        posttool(payload)
    elif event == "SubagentStop":
        subagent_stop(payload)
    elif event == "Stop":
        stop(payload)
    else:
        emit({})


if __name__ == "__main__":
    main()
