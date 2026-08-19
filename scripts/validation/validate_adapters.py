#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import tomllib
import uuid
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []

required = [
    root / "adapters" / "README.md",
    root / "adapters" / "codex" / "README.md",
    root / "adapters" / "codex" / "AGENTS.md",
    root / "adapters" / "codex" / "hooks" / "epistemic_gate.py",
    root / "adapters" / "codex" / "hooks" / "hooks.json",
    root / "adapters" / "codex" / "agents" / "thalarch-deliberator.toml",
    root / "adapters" / "codex" / "agents" / "thalarch-fact-checker.toml",
    root / "adapters" / "codex" / "agents" / "thalarch-verifier.toml",
    root / "adapters" / "claude" / "README.md",
    root / "adapters" / "claude" / "CLAUDE.md",
    root / "adapters" / "claude" / "hooks" / "epistemic_gate.py",
    root / "adapters" / "claude" / "settings.json",
    root / "adapters" / "claude" / "agents" / "thalarch-deliberator.md",
    root / "adapters" / "claude" / "agents" / "thalarch-fact-checker.md",
    root / "adapters" / "claude" / "agents" / "thalarch-verifier.md",
    root / "installers" / "install_adapter.py",
]

for path in required:
    if not path.is_file():
        errors.append(f"missing adapter file: {path.relative_to(root)}")

python_files = [
    root / "adapters" / "codex" / "hooks" / "epistemic_gate.py",
    root / "adapters" / "claude" / "hooks" / "epistemic_gate.py",
    root / "installers" / "install_adapter.py",
]
for path in python_files:
    if not path.is_file():
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        errors.append(f"syntax error in {path.relative_to(root)}: {exc}")

json_files = [
    root / "adapters" / "codex" / "hooks" / "hooks.json",
    root / "adapters" / "claude" / "settings.json",
]
parsed: dict[Path, dict] = {}
for path in json_files:
    if not path.is_file():
        continue
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        parsed[path] = data
        if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
            errors.append(f"{path.relative_to(root)} must have a top-level hooks object")
    except Exception as exc:
        errors.append(f"invalid JSON in {path.relative_to(root)}: {exc}")

codex_hooks = parsed.get(root / "adapters" / "codex" / "hooks" / "hooks.json", {}).get("hooks", {})
claude_hooks = parsed.get(root / "adapters" / "claude" / "settings.json", {}).get("hooks", {})
for label, hooks in [("Codex", codex_hooks), ("Claude", claude_hooks)]:
    if not isinstance(hooks, dict):
        continue
    for event in ["UserPromptSubmit", "PreToolUse", "PostToolUse", "SubagentStop", "Stop"]:
        if event not in hooks:
            errors.append(f"{label} adapter must wire {event}")
if isinstance(claude_hooks, dict) and "PostToolUseFailure" not in claude_hooks:
    errors.append("Claude adapter must wire PostToolUseFailure so failed verification invalidates stale success")

# Codex custom agents use native standalone TOML and stay structurally isolated from source edits.
codex_agents = root / "adapters" / "codex" / "agents"
for path in codex_agents.glob("thalarch-*.toml") if codex_agents.is_dir() else []:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid TOML in {path.relative_to(root)}: {exc}")
        continue
    for key in ["name", "description", "developer_instructions"]:
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{path.relative_to(root)} missing valid {key}")
    if data.get("sandbox_mode") != "read-only":
        errors.append(f"{path.relative_to(root)} must remain read-only")
    if data.get("model_reasoning_effort") != "high":
        errors.append(f"{path.relative_to(root)} must use high reasoning effort")

# Claude specialists must inherit the user's model, use high effort, and stay executable under
# normal permissions; plan mode would prevent the verifier from running real test/build commands.
claude_agents = root / "adapters" / "claude" / "agents"
for path in claude_agents.glob("thalarch-*.md") if claude_agents.is_dir() else []:
    text = path.read_text(encoding="utf-8")
    for key in ["name:", "description:", "tools:", "model:", "effort:", "permissionMode:"]:
        if key not in text:
            errors.append(f"{path.relative_to(root)} missing {key}")
    if not re.search(r"(?m)^model:\s*inherit\s*$", text):
        errors.append(f"{path.relative_to(root)} must use model: inherit for portability")
    if not re.search(r"(?m)^effort:\s*high\s*$", text):
        errors.append(f"{path.relative_to(root)} must use effort: high")
    if not re.search(r"(?m)^permissionMode:\s*default\s*$", text):
        errors.append(f"{path.relative_to(root)} must use permissionMode: default so evidence commands can execute")

# Canonical skills are copied verbatim to every host. Block known Antigravity-only assumptions in
# portable skills; host-specific adapter/agent directories are where those assumptions belong.
canonical_skills = root / "thalarch-mode" / "skills"
forbidden_core_phrases = {
    "current Antigravity session": "skill discovery must refer to the current host",
    "Antigravity exposes available skills": "skill discovery must be host-neutral",
    "Use Antigravity's native `generate_image`": "image generation must capability-detect the host",
    "**Antigravity `generate_image`**": "image routing must capability-detect the host",
    "using Antigravity's built-in Browser": "browser QA must capability-detect the host",
    "Prefer Antigravity's native Browser": "browser QA must capability-detect the host",
}
if canonical_skills.is_dir():
    for skill_md in canonical_skills.glob("*/SKILL.md"):
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        for phrase, explanation in forbidden_core_phrases.items():
            if phrase in text:
                errors.append(f"host-specific canonical skill assumption in {skill_md.relative_to(root)}: {explanation}")

# Permanent version policy applies to every adapter too.
newer = re.compile(r"(?i)\bThalarch(?:\s+(?:Mode|Orchestrator))?\s+v?[2-9]\d*(?:\.\d+)*\b")
for base in [root / "adapters", root / "installers"]:
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".py", ".txt", ".toml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if newer.search(text):
            errors.append(f"Thalarch adapter version must remain 1.0.0: {path.relative_to(root)}")


def run_hook(script: Path, data: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(data),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{script.name} exited {proc.returncode}: {proc.stderr or proc.stdout}")
    output = proc.stdout.strip()
    return json.loads(output) if output else {}


# Hook protocol regression tests:
# - mutation requires verification;
# - success after mutation clears the gate;
# - a newer mutation makes prior evidence stale;
# - a later failed verification invalidates an earlier success;
# - explicit UNVERIFIED is a safe escape when proof is unavailable.
if not errors:
    for host in ["codex", "claude"]:
        hook = root / "adapters" / host / "hooks" / "epistemic_gate.py"
        session = f"thalarch-adapter-test-{host}-{uuid.uuid4()}"
        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            common = {"session_id": session, "cwd": str(cwd)}

            try:
                if host == "codex":
                    mutate = {
                        **common,
                        "hook_event_name": "PostToolUse",
                        "tool_name": "apply_patch",
                        "tool_input": {"command": "*** Begin Patch"},
                        "tool_response": "Done!",
                    }
                    verify_success = {
                        **common,
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"command": "python -m pytest"},
                        "tool_response": "Process exited with code 0\nFinal output:\n12 passed",
                    }
                    verify_failure = {
                        **common,
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"command": "python -m pytest"},
                        "tool_response": "Process exited with code 1\nFinal output:\n1 failed",
                    }
                else:
                    mutate = {
                        **common,
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Edit",
                        "tool_input": {},
                        "tool_response": {"success": True},
                    }
                    verify_success = {
                        **common,
                        "hook_event_name": "PostToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"command": "python -m pytest"},
                        "tool_response": {"stdout": "12 passed", "stderr": "", "interrupted": False, "isImage": False},
                    }
                    verify_failure = {
                        **common,
                        "hook_event_name": "PostToolUseFailure",
                        "tool_name": "Bash",
                        "tool_input": {"command": "python -m pytest"},
                        "tool_response": "Exit code 1\n1 failed",
                    }

                run_hook(hook, mutate)
                blocked = run_hook(hook, {**common, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Done."})
                if blocked.get("decision") != "block":
                    errors.append(f"{host} Stop gate did not block mutation without fresh verification")

                run_hook(hook, verify_success)
                cleared = run_hook(hook, {**common, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Done."})
                if cleared.get("decision") == "block":
                    errors.append(f"{host} Stop gate did not accept successful verification after mutation")

                run_hook(hook, mutate)
                stale = run_hook(hook, {**common, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Done."})
                if stale.get("decision") != "block":
                    errors.append(f"{host} Stop gate reused stale verification after a newer mutation")

                run_hook(hook, verify_success)
                run_hook(hook, verify_failure)
                failed_latest = run_hook(hook, {**common, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Done."})
                if failed_latest.get("decision") != "block":
                    errors.append(f"{host} Stop gate ignored a later failed verification attempt")

                honest = run_hook(hook, {**common, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "Runtime result remains UNVERIFIED."})
                if honest.get("decision") == "block":
                    errors.append(f"{host} Stop gate did not allow an explicit UNVERIFIED completion state")
            except Exception as exc:
                errors.append(f"{host} hook protocol regression test failed: {exc}")

# Installer smoke tests: use temporary repositories and prove existing host instructions/config are preserved.
installer = root / "installers" / "install_adapter.py"
if installer.is_file() and not errors:
    for host in ["codex", "claude"]:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            if host == "codex":
                existing_instruction = repo / "AGENTS.md"
                existing_config = repo / ".codex" / "hooks.json"
                expected_skills = repo / ".agents" / "skills"
                expected_agents = repo / ".codex" / "agents"
                expected_agent_names = [
                    "thalarch-deliberator.toml",
                    "thalarch-fact-checker.toml",
                    "thalarch-verifier.toml",
                ]
                expected_companion = repo / "THALARCH.codex.md"
                expected_config_companion = repo / ".codex" / "THALARCH.hooks.json"
                expected_hook = repo / ".codex" / "hooks" / "thalarch_epistemic_gate.py"
            else:
                existing_instruction = repo / "CLAUDE.md"
                existing_config = repo / ".claude" / "settings.json"
                expected_skills = repo / ".claude" / "skills"
                expected_agents = repo / ".claude" / "agents"
                expected_agent_names = [
                    "thalarch-deliberator.md",
                    "thalarch-fact-checker.md",
                    "thalarch-verifier.md",
                ]
                expected_companion = repo / "THALARCH.claude.md"
                expected_config_companion = repo / ".claude" / "THALARCH.settings.json"
                expected_hook = repo / ".claude" / "hooks" / "thalarch_epistemic_gate.py"

            existing_instruction.write_text("KEEP-ME\n", encoding="utf-8")
            existing_config.parent.mkdir(parents=True, exist_ok=True)
            existing_config.write_text('{"existing": true}\n', encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(installer), host, "--scope", "repo", "--repo", str(repo)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                errors.append(f"{host} adapter installer smoke test failed: {proc.stderr or proc.stdout}")
                continue
            if existing_instruction.read_text(encoding="utf-8") != "KEEP-ME\n":
                errors.append(f"{host} installer overwrote an existing instruction file")
            if json.loads(existing_config.read_text(encoding="utf-8")) != {"existing": True}:
                errors.append(f"{host} installer overwrote an existing host config")
            if not expected_companion.is_file():
                errors.append(f"{host} installer did not create companion instructions")
            if not expected_config_companion.is_file():
                errors.append(f"{host} installer did not create companion hook config")
            if not expected_hook.is_file():
                errors.append(f"{host} installer did not install epistemic hook")
            if not expected_skills.is_dir() or not any(expected_skills.glob("thalarch-*/SKILL.md")):
                errors.append(f"{host} installer did not install canonical skills")
            for name in expected_agent_names:
                if not (expected_agents / name).is_file():
                    errors.append(f"{host} installer missing specialist agent: {name}")

if errors:
    print("THALARCH ADAPTER VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH ADAPTER VALIDATION PASSED")
print("version: 1.0.0 (fixed)")
print("canonical_core: host-capability-aware")
print("codex: skills + AGENTS + native custom agents + native hooks")
print("claude: skills + CLAUDE + non-editing executable custom agents + native hooks")
print("successful-fresh-evidence ordering: passed")
print("failed-verification invalidation: passed")
print("conservative installer: passed")
