#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SOURCE_PLUGIN = REPO_ROOT / "thalarch-mode"
DEFAULT_STAGED_PLUGIN = Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "thalarch-mode"

BEHAVIOR_EXTENSIONS = {".md", ".json", ".py", ".toml", ".yml", ".yaml", ".txt"}
BEHAVIOR_ROOT_FILES = {"plugin.json", "hooks.json"}
BEHAVIOR_DIRS = {"skills", "agents", "hooks"}
IGNORED_PARTS = {"__pycache__", ".git", ".thalarch-hook-state"}
IGNORED_NAMES = {".DS_Store"}


def is_behavior_path(rel: Path) -> bool:
    if len(rel.parts) == 1:
        return rel.name in BEHAVIOR_ROOT_FILES
    return rel.parts[0] in BEHAVIOR_DIRS


def behavior_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not root.is_dir():
        return files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if not is_behavior_path(rel):
            continue
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        if path.name in IGNORED_NAMES or path.suffix.lower() == ".pyc":
            continue
        if path.suffix.lower() not in BEHAVIOR_EXTENSIONS:
            continue
        files[rel.as_posix()] = path
    return files


def fingerprint(files: dict[str, Path]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(files[rel].read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def verify_plugin_tree(staged_root: Path | None = None) -> dict[str, Any]:
    staged_root = staged_root or DEFAULT_STAGED_PLUGIN
    source = behavior_files(SOURCE_PLUGIN)
    staged = behavior_files(staged_root)

    if not source:
        return {
            "match": False,
            "reason": f"source plugin not found or empty: {SOURCE_PLUGIN}",
            "source_root": str(SOURCE_PLUGIN),
            "staged_root": str(staged_root),
        }
    if not staged:
        return {
            "match": False,
            "reason": f"staged CLI plugin not found or empty: {staged_root}",
            "source_root": str(SOURCE_PLUGIN),
            "staged_root": str(staged_root),
            "source_fingerprint": fingerprint(source),
        }

    source_names = set(source)
    staged_names = set(staged)
    missing = sorted(source_names - staged_names)
    extra = sorted(staged_names - source_names)
    mismatched = sorted(
        rel for rel in source_names & staged_names
        if source[rel].read_bytes() != staged[rel].read_bytes()
    )

    source_fingerprint = fingerprint(source)
    staged_fingerprint = fingerprint(staged)
    match = not missing and not extra and not mismatched and source_fingerprint == staged_fingerprint
    return {
        "match": match,
        "reason": "exact behavior-file match" if match else "staged plugin differs from benchmark checkout",
        "source_root": str(SOURCE_PLUGIN),
        "staged_root": str(staged_root),
        "source_fingerprint": source_fingerprint,
        "staged_fingerprint": staged_fingerprint,
        "source_file_count": len(source),
        "staged_file_count": len(staged),
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
    }


def format_mismatch(result: dict[str, Any], limit: int = 8) -> str:
    lines = [str(result.get("reason", "plugin integrity check failed"))]
    lines.append(f"source: {result.get('source_root', '?')}")
    lines.append(f"staged: {result.get('staged_root', '?')}")
    for label in ("missing", "extra", "mismatched"):
        values = result.get(label) or []
        if not values:
            continue
        shown = ", ".join(str(v) for v in values[:limit])
        suffix = " ..." if len(values) > limit else ""
        lines.append(f"{label} ({len(values)}): {shown}{suffix}")
    return "\n".join(lines)
