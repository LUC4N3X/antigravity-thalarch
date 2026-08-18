#!/usr/bin/env python3
"""Block high-confidence invented project commands before execution.

This gate deliberately checks only things that can be validated cheaply and
reliably from the workspace. It does not try to prove arbitrary shell commands
correct; uncertain cases are allowed and remain subject to runtime verification.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from hook_utils import emit, find_nearest_file, read_payload, resolve_existing_path


def command_line(args: dict[str, Any]) -> str:
    for key in ("CommandLine", "commandLine", "command", "cmd"):
        value = args.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def deny(reason: str) -> None:
    emit({"decision": "deny", "reason": f"Thalarch command evidence gate: {reason}"})


def load_package_scripts(payload: dict[str, Any], args: dict[str, Any]) -> tuple[Path | None, set[str]]:
    package = find_nearest_file("package.json", payload, args)
    if not package:
        return None, set()
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
        scripts = data.get("scripts") if isinstance(data, dict) else {}
        if not isinstance(scripts, dict):
            return package, set()
        return package, {str(key) for key in scripts.keys()}
    except Exception:
        return package, set()


def require_existing_script(raw: str, payload: dict[str, Any], args: dict[str, Any], label: str) -> bool:
    if resolve_existing_path(raw, payload, args) is not None:
        return True
    deny(
        f"{label} references a local script/file that does not exist: {raw}. "
        "Inspect the repository and derive the real path first."
    )
    return False


def main() -> None:
    payload = read_payload()
    call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
    if str(call.get("name") or "") != "run_command":
        emit({"decision": "allow"})
        return

    args = call.get("args") if isinstance(call.get("args"), dict) else {}
    command = command_line(args)
    if not command:
        emit({"decision": "allow"})
        return

    # A declared working directory is an exact repository/environment claim.
    for key in ("Cwd", "cwd", "WorkingDirectory", "workingDirectory"):
        raw_cwd = args.get(key)
        if isinstance(raw_cwd, str) and raw_cwd.strip():
            cwd = Path(raw_cwd).expanduser()
            if not cwd.exists() or not cwd.is_dir():
                deny(
                    f"working directory does not exist: {raw_cwd}. "
                    "Search/select the real workspace before running commands."
                )
                return
            break

    normalized = command.strip()

    # Repository-local wrappers must physically exist.
    wrapper_rules = [
        (r"^(?:\.\\|\./)?gradlew(?:\.bat)?\b", ("gradlew", "gradlew.bat"), "Gradle wrapper"),
        (r"^(?:\.\\|\./)?mvnw(?:\.cmd)?\b", ("mvnw", "mvnw.cmd"), "Maven wrapper"),
    ]
    for pattern, filenames, label in wrapper_rules:
        if re.search(pattern, normalized, flags=re.I):
            if not any(find_nearest_file(filename, payload, args) for filename in filenames):
                deny(
                    f"{label} command was proposed but no matching wrapper exists in/above the "
                    "current workspace. Discover the repository's actual build tool first."
                )
                return

    # npm/pnpm/yarn project scripts: deny an exact script name that package.json does not declare.
    script_patterns = [
        (r"^npm\s+run\s+([^\s;&|]+)", "npm"),
        (r"^pnpm\s+(?:run\s+)?([^\s;&|]+)", "pnpm"),
        (r"^yarn\s+(?:run\s+)?([^\s;&|]+)", "yarn"),
    ]
    for pattern, manager in script_patterns:
        match = re.search(pattern, normalized, flags=re.I)
        if not match:
            continue
        script = match.group(1).strip("\"'")
        # Manager-native commands are not package scripts.
        if script.lower() in {
            "install", "add", "remove", "update", "upgrade", "dlx", "exec", "init",
            "publish", "pack", "link", "unlink", "config", "cache", "why", "list", "ls",
        }:
            break
        package, scripts = load_package_scripts(payload, args)
        if package is None:
            deny(
                f"{manager} script '{script}' was proposed but no package.json was found for the "
                "current workspace."
            )
            return
        if script not in scripts:
            deny(
                f"{manager} script '{script}' is not declared in {package}. Read package.json and "
                "use a real repository script instead of guessing."
            )
            return
        break

    # npm test is shorthand; require an explicit test script so it cannot be treated as project-native by memory.
    if re.search(r"^npm\s+(?:test|t)(?:\s|$)", normalized, flags=re.I):
        package, scripts = load_package_scripts(payload, args)
        if package is None or "test" not in scripts:
            deny(
                "'npm test' was proposed without a declared package.json test script. "
                "Discover the repository's actual test command first."
            )
            return

    # Commands that execute a repository script must point at an existing file.
    path_patterns = [
        (r"^(?:python3?|py(?:\s+-3)?)\s+(?!-m\b)(?:-u\s+)?[\"']?([^\"'\s;&|]+\.py)\b", "Python"),
        (r"^node\s+[\"']?([^\"'\s;&|]+\.(?:js|mjs|cjs))\b", "Node"),
        (r"^(?:bash|sh)\s+[\"']?([^\"'\s;&|]+\.(?:sh|bash))\b", "shell"),
        (r"^(?:pwsh|powershell)(?:\.exe)?\b[^\n]*?\s-(?:File|f)\s+[\"']?([^\"'\s;&|]+\.ps1)\b", "PowerShell"),
        (r"^(?:\.\\|\./)([^\s;&|]+\.(?:sh|bash|ps1|py|js|mjs|cjs))\b", "direct script"),
    ]
    for pattern, label in path_patterns:
        match = re.search(pattern, normalized, flags=re.I)
        if match and not require_existing_script(match.group(1), payload, args, label):
            return

    compose_match = re.search(
        r"\bdocker\s+compose\b[^\n]*?\s-f\s+[\"']?([^\"'\s;&|]+)",
        normalized,
        flags=re.I,
    )
    if compose_match and resolve_existing_path(compose_match.group(1), payload, args) is None:
        deny(f"docker compose references a file that does not exist: {compose_match.group(1)}.")
        return

    # Git operations (except init/clone) should run in an actual Git worktree/repository.
    git_match = re.search(r"^git\s+([^\s;&|]+)", normalized, flags=re.I)
    if git_match and git_match.group(1).lower() not in {"init", "clone", "--version", "help"}:
        git_root = find_nearest_file(".git", payload, args)
        if git_root is None:
            deny(
                f"git {git_match.group(1)} was proposed outside a detected Git repository. "
                "Confirm the correct repository/workspace first."
            )
            return

    emit({"decision": "allow"})


if __name__ == "__main__":
    main()
