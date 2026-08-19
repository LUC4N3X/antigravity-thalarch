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


def state_file(data: dict) -> Path:
    sid = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(data.get("session_id") or "unknown"))
    root = Path(tempfile.gettempdir()) / "thalarch-claude"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{sid}.json"


def load(data: dict) -> dict:
    p = state_file(data)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"mutation": 0, "verification": 0, "subagents": 0}
    except Exception:
        return {"mutation": 0, "verification": 0, "subagents": 0}


def save(data: dict, state: dict) -> None:
    state_file(data).write_text(json.dumps(state, indent=2), encoding="utf-8")


def command(data: dict) -> str:
    inp = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    return str(inp.get("command") or "").strip()


def pretool(data: dict) -> None:
    tool = str(data.get("tool_name") or "")
    if tool not in {"Bash", "PowerShell"}:
        return
    cmd = command(data)
    cwd = Path(str(data.get("cwd") or os.getcwd())).expanduser()
    if re.match(r"^(?:\./)?gradlew(?:\.bat)?\b", cmd, re.I) and not ((cwd / "gradlew").exists() or (cwd / "gradlew.bat").exists()):
        emit({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Thalarch: Gradle wrapper was guessed but does not exist here. Discover the real build tool first."}})
        return
    npm = re.match(r"^npm\s+run\s+([^\s;&|]+)", cmd, re.I)
    if npm:
        package = cwd / "package.json"
        scripts = set()
        if package.is_file():
            try:
                raw = json.loads(package.read_text(encoding="utf-8"))
                scripts = set((raw.get("scripts") or {}).keys())
            except Exception:
                pass
        name = npm.group(1).strip("\"'")
        if name not in scripts:
            emit({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":f"Thalarch: npm script '{name}' is not declared in package.json. Inspect project scripts first."}})


def posttool(data: dict) -> None:
    state = load(data)
    tool = str(data.get("tool_name") or "")
    cmd = command(data)
    if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        state["mutation"] += 1
    if tool in {"Bash", "PowerShell"}:
        if re.search(r"\b(test|check|lint|typecheck|build|compile|verify|pytest|unittest|gradle|mvn|cargo\s+test|go\s+test)\b", cmd, re.I):
            state["verification"] += 1
    save(data, state)


def stop(data: dict) -> None:
    if bool(data.get("stop_hook_active")):
        return
    state = load(data)
    msg = str(data.get("last_assistant_message") or "")
    if state.get("mutation", 0) and not state.get("verification", 0) and "unverified" not in msg.lower():
        emit({"decision":"block","reason":"THALARCH EVIDENCE GATE: code mutation was observed without fresh project-native verification. Run the strongest available test/build/check, or explicitly keep the affected completion claim UNVERIFIED."})


def main() -> None:
    data = payload()
    event = str(data.get("hook_event_name") or "")
    if event == "UserPromptSubmit":
        emit({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Thalarch 1.0.0: verify cheap facts before asserting them; ground version-sensitive APIs; never invent paths, commands, test/CI/publication results or visual state; use UNKNOWN/UNVERIFIED when evidence is missing; seek disconfirming evidence on difficult work."}})
    elif event == "PreToolUse":
        pretool(data)
    elif event == "PostToolUse":
        posttool(data)
    elif event == "SubagentStop":
        state = load(data); state["subagents"] += 1; save(data, state)
    elif event == "Stop":
        stop(data)


if __name__ == "__main__":
    main()
