#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SOURCE_PLUGIN = REPO_ROOT / "thalarch-mode"
PLUGIN_NAME = "thalarch-mode"

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


def known_staged_candidates() -> list[Path]:
    """Return documented and compatibility locations for Antigravity plugin staging."""
    home = Path.home()
    candidates = [
        # Antigravity CLI documentation.
        home / ".gemini" / "antigravity-cli" / "plugins" / PLUGIN_NAME,
        # Antigravity global-plugin documentation / newer shared config layout.
        home / ".gemini" / "config" / "plugins" / PLUGIN_NAME,
        # Compatibility paths seen across Gemini/Antigravity config migrations.
        home / ".gemini" / "plugins" / PLUGIN_NAME,
    ]

    for env_name in ("LOCALAPPDATA", "APPDATA"):
        value = os.environ.get(env_name)
        if not value:
            continue
        base = Path(value)
        candidates.extend([
            base / "agy" / "plugins" / PLUGIN_NAME,
            base / "Google" / "Antigravity" / "plugins" / PLUGIN_NAME,
        ])

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _bounded_plugin_search(root: Path, max_depth: int = 6) -> Iterable[Path]:
    """Find plugin roots without recursively walking an entire user profile."""
    if not root.is_dir():
        return []

    found: list[Path] = []
    root_depth = len(root.parts)
    try:
        for current, dirs, _files in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            if depth >= max_depth:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in IGNORED_PARTS]
            if current_path.name == PLUGIN_NAME and (current_path / "plugin.json").is_file():
                found.append(current_path)
                dirs[:] = []
    except OSError:
        pass
    return found


def discover_staged_candidates() -> list[Path]:
    candidates = list(known_staged_candidates())

    search_roots = [Path.home() / ".gemini"]
    for env_name in ("LOCALAPPDATA", "APPDATA"):
        value = os.environ.get(env_name)
        if value:
            search_roots.append(Path(value) / "agy")
            search_roots.append(Path(value) / "Google" / "Antigravity")

    for root in search_roots:
        candidates.extend(_bounded_plugin_search(root))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve() if candidate.exists() else candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def compare_plugin_trees(source_root: Path, staged_root: Path) -> dict[str, Any]:
    source = behavior_files(source_root)
    staged = behavior_files(staged_root)

    if not source:
        return {
            "match": False,
            "reason": f"source plugin not found or empty: {source_root}",
            "source_root": str(source_root),
            "staged_root": str(staged_root),
        }
    if not staged:
        return {
            "match": False,
            "reason": f"staged plugin not found or empty: {staged_root}",
            "source_root": str(source_root),
            "staged_root": str(staged_root),
            "source_fingerprint": fingerprint(source),
            "source_file_count": len(source),
            "staged_file_count": 0,
            "missing": sorted(source),
            "extra": [],
            "mismatched": [],
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
        "source_root": str(source_root),
        "staged_root": str(staged_root),
        "source_fingerprint": source_fingerprint,
        "staged_fingerprint": staged_fingerprint,
        "source_file_count": len(source),
        "staged_file_count": len(staged),
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
    }


def _mismatch_cost(result: dict[str, Any]) -> int:
    return (
        len(result.get("missing") or [])
        + len(result.get("extra") or [])
        + len(result.get("mismatched") or [])
        + (100000 if int(result.get("staged_file_count") or 0) == 0 else 0)
    )


def verify_plugin_tree(
    staged_root: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, Any]:
    """Verify the behavior-bearing plugin tree actually staged by Antigravity.

    With no staged_root override, discover documented/compatible locations and accept only an
    exact byte-for-byte behavior-file match. This avoids coupling benchmark integrity to one CLI
    filesystem layout while still proving the tested plugin matches the checkout.
    """
    source_root = source_root or SOURCE_PLUGIN
    source = behavior_files(source_root)
    if not source:
        return {
            "match": False,
            "reason": f"source plugin not found or empty: {source_root}",
            "source_root": str(source_root),
            "staged_root": str(staged_root) if staged_root else "auto-discovery",
        }

    candidates = [staged_root] if staged_root is not None else discover_staged_candidates()
    comparisons: list[dict[str, Any]] = []
    for candidate in candidates:
        result = compare_plugin_trees(source_root, candidate)
        comparisons.append(result)
        if result.get("match") is True:
            result["discovery"] = "explicit" if staged_root is not None else "auto"
            result["candidate_count"] = len(candidates)
            result["candidate_roots"] = [str(path) for path in candidates]
            return result

    existing = [result for result in comparisons if int(result.get("staged_file_count") or 0) > 0]
    if existing:
        best = min(existing, key=_mismatch_cost)
        best = dict(best)
        best["reason"] = "no discovered staged plugin exactly matches the benchmark checkout"
    else:
        best = {
            "match": False,
            "reason": "no staged Antigravity CLI plugin copy was discovered",
            "source_root": str(source_root),
            "staged_root": "auto-discovery" if staged_root is None else str(staged_root),
            "source_fingerprint": fingerprint(source),
            "source_file_count": len(source),
            "staged_file_count": 0,
            "missing": [],
            "extra": [],
            "mismatched": [],
        }

    best["candidate_count"] = len(candidates)
    best["candidate_roots"] = [str(path) for path in candidates]
    return best


def format_mismatch(result: dict[str, Any], limit: int = 8) -> str:
    lines = [str(result.get("reason", "plugin integrity check failed"))]
    lines.append(f"source: {result.get('source_root', '?')}")
    lines.append(f"staged: {result.get('staged_root', '?')}")
    candidates = result.get("candidate_roots") or []
    if candidates:
        lines.append(f"searched candidates ({len(candidates)}):")
        for candidate in candidates[:limit]:
            lines.append(f"  - {candidate}")
        if len(candidates) > limit:
            lines.append("  - ...")
    for label in ("missing", "extra", "mismatched"):
        values = result.get(label) or []
        if not values:
            continue
        shown = ", ".join(str(v) for v in values[:limit])
        suffix = " ..." if len(values) > limit else ""
        lines.append(f"{label} ({len(values)}): {shown}{suffix}")
    return "\n".join(lines)
