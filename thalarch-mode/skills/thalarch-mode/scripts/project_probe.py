#!/usr/bin/env python3
"""Read-only project snapshot for Thalarch Mode."""

from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path

BUILD_MARKERS = [
    "settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts",
    "gradlew", "gradlew.bat", "package.json", "pnpm-lock.yaml", "yarn.lock",
    "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml",
    "Makefile", "CMakeLists.txt",
]

RULE_FILES = ["AGENTS.md", "GEMINI.md", "CLAUDE.md", "CONTRIBUTING.md", "README.md"]

def cmd(cwd: Path, *args: str) -> dict:
    try:
        p = subprocess.run(
            list(args), cwd=cwd, capture_output=True, text=True,
            timeout=8, check=False
        )
        return {
            "command": " ".join(args),
            "exit": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        }
    except Exception as exc:
        return {"command": " ".join(args), "error": str(exc)}

def main() -> int:
    ap = argparse.ArgumentParser(description="Print a read-only project snapshot.")
    ap.add_argument("--path", default=".", help="Workspace/repository path")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    ns = ap.parse_args()

    root = Path(ns.path).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")

    snapshot = {
        "workspace": str(root),
        "rules_present": [f for f in RULE_FILES if (root / f).exists()],
        "build_markers": [f for f in BUILD_MARKERS if (root / f).exists()],
        "workspace_rules": sorted(
            str(p.relative_to(root))
            for p in (root / ".agents" / "rules").glob("*.md")
        ) if (root / ".agents" / "rules").exists() else [],
    }

    if (root / ".git").exists() or cmd(root, "git", "rev-parse", "--is-inside-work-tree").get("exit") == 0:
        snapshot["git"] = {
            "root": cmd(root, "git", "rev-parse", "--show-toplevel"),
            "branch": cmd(root, "git", "branch", "--show-current"),
            "status": cmd(root, "git", "status", "--short"),
            "changed_files": cmd(root, "git", "diff", "--name-only"),
            "recent_commits": cmd(root, "git", "log", "-5", "--oneline"),
        }
    else:
        snapshot["git"] = {"detected": False}

    if ns.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(f"Workspace: {snapshot['workspace']}")
        print("Rules:", ", ".join(snapshot["rules_present"] + snapshot["workspace_rules"]) or "none detected")
        print("Build markers:", ", ".join(snapshot["build_markers"]) or "none detected")
        git = snapshot["git"]
        if git.get("detected") is False:
            print("Git: not detected")
        else:
            print("Branch:", git["branch"].get("stdout") or "(detached/unknown)")
            print("Dirty status:")
            print(git["status"].get("stdout") or "(clean)")
            print("Changed files:")
            print(git["changed_files"].get("stdout") or "(none)")
            print("Recent commits:")
            print(git["recent_commits"].get("stdout") or "(none)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
