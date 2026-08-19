#!/usr/bin/env python3
"""Install Thalarch 1.0.0 adapters for Codex or Claude Code.

The installer is intentionally conservative:
- canonical Thalarch skills are copied from thalarch-mode/skills;
- only thalarch-* skill/agent directories are replaced, with backups;
- existing AGENTS.md / CLAUDE.md / hook settings are never overwritten;
- when a host config already exists, a THALARCH companion template is written instead.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILLS = ROOT / "thalarch-mode" / "skills"
ADAPTERS = ROOT / "adapters"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.backup-{stamp()}")


def backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = backup_path(path)
    shutil.move(str(path), str(backup))
    return backup


def copy_tree_replacing(source: Path, destination: Path) -> Path | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_existing(destination)
    shutil.copytree(source, destination)
    return backup


def copy_skills(target: Path) -> tuple[int, list[tuple[Path, Path]]]:
    target.mkdir(parents=True, exist_ok=True)
    backups: list[tuple[Path, Path]] = []
    count = 0
    for source in sorted(CANONICAL_SKILLS.iterdir()):
        if not source.is_dir() or not source.name.startswith("thalarch-"):
            continue
        destination = target / source.name
        backup = copy_tree_replacing(source, destination)
        if backup:
            backups.append((destination, backup))
        count += 1
    return count, backups


def python_command(script: Path) -> str:
    exe = Path(sys.executable).resolve()
    return f'"{exe}" "{script.resolve()}"'


def codex_hook_config(script: Path) -> dict:
    command = python_command(script)
    hook = {"type": "command", "command": command, "timeout": 10}
    return {
        "description": f"Thalarch {VERSION} anti-hallucination evidence gates.",
        "hooks": {
            "UserPromptSubmit": [{"hooks": [dict(hook, statusMessage="Loading Thalarch evidence contract")]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [dict(hook, statusMessage="Grounding command against project evidence")]}],
            "PostToolUse": [{"matcher": "Bash|apply_patch", "hooks": [hook]}],
            "SubagentStop": [{"hooks": [hook]}],
            "Stop": [{"hooks": [dict(hook, timeout=15, statusMessage="Checking completion evidence")]}],
        },
    }


def claude_hook_config(script: Path) -> dict:
    command = python_command(script)
    hook = {"type": "command", "command": command, "timeout": 10}
    return {
        "hooks": {
            "UserPromptSubmit": [{"hooks": [hook]}],
            "PreToolUse": [{"matcher": "Bash|PowerShell", "hooks": [hook]}],
            "PostToolUse": [{"matcher": "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit", "hooks": [hook]}],
            "SubagentStop": [{"hooks": [hook]}],
            "Stop": [{"hooks": [dict(hook, timeout=15)]}],
        }
    }


def write_json_conservatively(primary: Path, companion: Path, data: dict) -> tuple[Path, bool]:
    primary.parent.mkdir(parents=True, exist_ok=True)
    target = companion if primary.exists() else primary
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target, target == primary


def install_instruction_file(source: Path, primary: Path, companion_name: str) -> tuple[Path, bool]:
    primary.parent.mkdir(parents=True, exist_ok=True)
    if primary.exists():
        target = primary.parent / companion_name
        shutil.copy2(source, target)
        return target, False
    shutil.copy2(source, primary)
    return primary, True


def install_codex(base: Path, user_scope: bool) -> dict:
    skills_target = (Path.home() / ".agents" / "skills") if user_scope else (base / ".agents" / "skills")
    codex_root = (Path.home() / ".codex") if user_scope else (base / ".codex")
    instruction_primary = (Path.home() / ".codex" / "AGENTS.md") if user_scope else (base / "AGENTS.md")

    skill_count, skill_backups = copy_skills(skills_target)

    hook_source = ADAPTERS / "codex" / "hooks" / "epistemic_gate.py"
    hook_target = codex_root / "hooks" / "thalarch_epistemic_gate.py"
    hook_target.parent.mkdir(parents=True, exist_ok=True)
    hook_backup = backup_existing(hook_target)
    shutil.copy2(hook_source, hook_target)

    config_primary = codex_root / "hooks.json"
    config_companion = codex_root / "THALARCH.hooks.json"
    config_target, config_active = write_json_conservatively(
        config_primary,
        config_companion,
        codex_hook_config(hook_target),
    )

    instruction_target, instruction_active = install_instruction_file(
        ADAPTERS / "codex" / "AGENTS.md",
        instruction_primary,
        "THALARCH.codex.md",
    )

    return {
        "host": "codex",
        "skills": skill_count,
        "skills_target": str(skills_target),
        "skill_backups": [(str(dst), str(bak)) for dst, bak in skill_backups],
        "hook": str(hook_target),
        "hook_backup": str(hook_backup) if hook_backup else None,
        "config": str(config_target),
        "config_active": config_active,
        "instruction": str(instruction_target),
        "instruction_active": instruction_active,
    }


def install_claude(base: Path, user_scope: bool) -> dict:
    claude_root = (Path.home() / ".claude") if user_scope else (base / ".claude")
    skills_target = claude_root / "skills"
    instruction_primary = (Path.home() / ".claude" / "CLAUDE.md") if user_scope else (base / "CLAUDE.md")

    skill_count, skill_backups = copy_skills(skills_target)

    hook_source = ADAPTERS / "claude" / "hooks" / "epistemic_gate.py"
    hook_target = claude_root / "hooks" / "thalarch_epistemic_gate.py"
    hook_target.parent.mkdir(parents=True, exist_ok=True)
    hook_backup = backup_existing(hook_target)
    shutil.copy2(hook_source, hook_target)

    agents_target = claude_root / "agents"
    agents_target.mkdir(parents=True, exist_ok=True)
    agent_backups: list[tuple[str, str]] = []
    agent_count = 0
    for source in sorted((ADAPTERS / "claude" / "agents").glob("thalarch-*.md")):
        destination = agents_target / source.name
        backup = backup_existing(destination)
        if backup:
            agent_backups.append((str(destination), str(backup)))
        shutil.copy2(source, destination)
        agent_count += 1

    config_primary = claude_root / "settings.json"
    config_companion = claude_root / "THALARCH.settings.json"
    config_target, config_active = write_json_conservatively(
        config_primary,
        config_companion,
        claude_hook_config(hook_target),
    )

    instruction_target, instruction_active = install_instruction_file(
        ADAPTERS / "claude" / "CLAUDE.md",
        instruction_primary,
        "THALARCH.claude.md",
    )

    return {
        "host": "claude",
        "skills": skill_count,
        "skills_target": str(skills_target),
        "skill_backups": [(str(dst), str(bak)) for dst, bak in skill_backups],
        "agents": agent_count,
        "agents_target": str(agents_target),
        "agent_backups": agent_backups,
        "hook": str(hook_target),
        "hook_backup": str(hook_backup) if hook_backup else None,
        "config": str(config_target),
        "config_active": config_active,
        "instruction": str(instruction_target),
        "instruction_active": instruction_active,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Install Thalarch {VERSION} host adapters")
    parser.add_argument("host", choices=["codex", "claude"])
    parser.add_argument("--scope", choices=["user", "repo"], default="user")
    parser.add_argument("--repo", type=Path, help="Repository path for --scope repo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not CANONICAL_SKILLS.is_dir():
        raise SystemExit(f"Canonical skill directory not found: {CANONICAL_SKILLS}")

    user_scope = args.scope == "user"
    if user_scope:
        base = Path.home()
    else:
        if args.repo is None:
            raise SystemExit("--repo PATH is required with --scope repo")
        base = args.repo.expanduser().resolve()
        if not base.is_dir():
            raise SystemExit(f"Repository directory does not exist: {base}")

    result = install_codex(base, user_scope) if args.host == "codex" else install_claude(base, user_scope)

    print(f"Thalarch {VERSION} adapter installed for {result['host']} ({args.scope} scope).")
    print(f"Skills: {result['skills']} -> {result['skills_target']}")
    if "agents" in result:
        print(f"Claude subagents: {result['agents']} -> {result['agents_target']}")
    print(f"Epistemic hook: {result['hook']}")
    print(f"Instructions: {result['instruction']}")
    print(f"Hook config: {result['config']}")

    if not result["instruction_active"]:
        print("NOTE: an existing host instruction file was preserved. Merge/reference the THALARCH companion file if you want the persistent instruction layer active.")
    if not result["config_active"]:
        print("NOTE: an existing host hook config was preserved. Review and merge the THALARCH hook template into the existing configuration before expecting hard gates to run.")
    if args.host == "codex":
        print("Codex may require you to review/trust the installed hooks before they execute.")
    print("Restart/reload the host after installation.")


if __name__ == "__main__":
    main()
