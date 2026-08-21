#!/usr/bin/env python3
"""Create and verify a byte-level lock for Thalarch behavior-bearing assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EXTENSIONS = {".md", ".json", ".py", ".toml", ".yml", ".yaml", ".txt"}
ROOT_FILES = {"plugin.json", "hooks.json"}
DIRS = {"skills", "agents", "hooks"}
IGNORED_PARTS = {"__pycache__", ".git", ".thalarch-hook-state"}
IGNORED_NAMES = {".DS_Store", "behavior-lock.json"}


def behavior_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in root.rglob("*") if root.is_dir() else []:
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if path.name in IGNORED_NAMES or any(part in IGNORED_PARTS for part in rel.parts):
            continue
        allowed = (len(rel.parts) == 1 and rel.name in ROOT_FILES) or (len(rel.parts) > 1 and rel.parts[0] in DIRS)
        if not allowed or path.suffix.lower() not in EXTENSIONS:
            continue
        result[rel.as_posix()] = path
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_manifest(root: Path) -> dict[str, object]:
    files = behavior_files(root)
    return {
        "schema_version": 1,
        "algorithm": "sha256",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": {rel: sha256(path) for rel, path in sorted(files.items())},
    }


def verify(root: Path, manifest: dict[str, object]) -> dict[str, object]:
    expected_raw = manifest.get("files")
    expected = expected_raw if isinstance(expected_raw, dict) else {}
    current = behavior_files(root)
    current_names = set(current)
    expected_names = {str(name) for name in expected}
    missing = sorted(expected_names - current_names)
    extra = sorted(current_names - expected_names)
    mismatched = sorted(
        name for name in expected_names & current_names
        if str(expected.get(name)) != sha256(current[name])
    )
    return {
        "match": not missing and not extra and not mismatched,
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
        "current_file_count": len(current),
        "expected_file_count": len(expected_names),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or verify a Thalarch behavior lock")
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("root", type=Path)
    write.add_argument("--output", type=Path, default=None)

    check = sub.add_parser("verify")
    check.add_argument("root", type=Path)
    check.add_argument("--lock", type=Path, default=None)

    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "write":
        output = (args.output or (root / "behavior-lock.json")).resolve()
        manifest = make_manifest(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"THALARCH BEHAVIOR LOCK WRITTEN: {output}")
        print(f"files: {manifest['file_count']}")
        return

    lock = (args.lock or (root / "behavior-lock.json")).resolve()
    if not lock.is_file():
        raise SystemExit(f"behavior lock not found: {lock}")
    manifest = json.loads(lock.read_text(encoding="utf-8"))
    result = verify(root, manifest if isinstance(manifest, dict) else {})
    if not result["match"]:
        print("THALARCH BEHAVIOR LOCK MISMATCH")
        for key in ("missing", "extra", "mismatched"):
            values = result[key]
            if values:
                print(f"{key}: {', '.join(values[:20])}")
        raise SystemExit(1)
    print("THALARCH BEHAVIOR LOCK VERIFIED")
    print(f"files: {result['current_file_count']}")


if __name__ == "__main__":
    main()
