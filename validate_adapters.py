#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []

required = [
    root / "adapters" / "README.md",
    root / "adapters" / "codex" / "README.md",
    root / "adapters" / "codex" / "AGENTS.md",
    root / "adapters" / "codex" / "hooks" / "epistemic_gate.py",
    root / "adapters" / "codex" / "hooks" / "hooks.json",
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

# Claude agent frontmatter stays intentionally small and native.
for path in (root / "adapters" / "claude" / "agents").glob("thalarch-*.md") if (root / "adapters" / "claude" / "agents").is_dir() else []:
    text = path.read_text(encoding="utf-8")
    for key in ["name:", "description:", "tools:", "model:", "permissionMode:"]:
        if key not in text:
            errors.append(f"{path.relative_to(root)} missing {key}")

# Permanent version policy applies to every adapter too.
newer = re.compile(r"(?i)\bThalarch(?:\s+(?:Mode|Orchestrator))?\s+v?[2-9]\d*(?:\.\d+)*\b")
for base in [root / "adapters", root / "installers"]:
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".py", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if newer.search(text):
            errors.append(f"Thalarch adapter version must remain 1.0.0: {path.relative_to(root)}")

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
                expected_companion = repo / "THALARCH.codex.md"
                expected_config_companion = repo / ".codex" / "THALARCH.hooks.json"
                expected_hook = repo / ".codex" / "hooks" / "thalarch_epistemic_gate.py"
            else:
                existing_instruction = repo / "CLAUDE.md"
                existing_config = repo / ".claude" / "settings.json"
                expected_skills = repo / ".claude" / "skills"
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
            if host == "claude":
                agents = repo / ".claude" / "agents"
                for name in ["thalarch-deliberator.md", "thalarch-fact-checker.md", "thalarch-verifier.md"]:
                    if not (agents / name).is_file():
                        errors.append(f"Claude installer missing agent: {name}")

if errors:
    print("THALARCH ADAPTER VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH ADAPTER VALIDATION PASSED")
print("version: 1.0.0 (fixed)")
print("codex: skills + AGENTS + native hooks")
print("claude: skills + CLAUDE + subagents + native hooks")
print("conservative installer: passed")
