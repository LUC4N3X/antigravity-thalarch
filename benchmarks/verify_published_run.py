#!/usr/bin/env python3
"""Verify a sanitized benchmark publication manifest and optional source run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("attestation_sha256", None)
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def recompute_aggregate(entries: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in entries:
        groups.setdefault(str(item.get("mode") or "unknown"), []).append(item)
    result: dict[str, Any] = {}
    for mode, rows in sorted(groups.items()):
        n = len(rows)
        passed = sum(str(row.get("task_status") or "").upper() == "PASS" for row in rows)
        hallucinations = sum(int(row.get("hallucinations") or 0) for row in rows)
        walls = [float(row["wall_seconds"]) for row in rows if isinstance(row.get("wall_seconds"), (int, float))]
        result[mode] = {
            "n": n,
            "task_pass_percent": round(100 * passed / n, 1) if n else None,
            "hallucinations": hallucinations,
            "avg_wall_seconds": round(sum(walls) / len(walls), 3) if walls else None,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a Thalarch public benchmark manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("public manifest must be an object")
    expected_attestation = str(payload.get("attestation_sha256") or "")
    actual_attestation = canonical_hash(payload)
    if not expected_attestation or expected_attestation != actual_attestation:
        raise SystemExit(f"public manifest attestation mismatch: expected {expected_attestation}, got {actual_attestation}")

    entries = payload.get("results") if isinstance(payload.get("results"), list) else []
    if len(entries) != int(payload.get("result_count") or -1):
        raise SystemExit("public manifest result_count does not match results array")
    aggregate = recompute_aggregate([item for item in entries if isinstance(item, dict)])
    if aggregate != payload.get("aggregate"):
        raise SystemExit("public manifest aggregate does not match its result entries")

    if args.run_dir is not None:
        run_dir = args.run_dir.resolve()
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            raise SystemExit(f"source run manifest missing: {manifest_path}")
        if sha256(manifest_path) != payload.get("source_manifest_sha256"):
            raise SystemExit("source manifest SHA-256 differs from public manifest")
        for item in entries:
            if not isinstance(item, dict):
                raise SystemExit("result entry must be an object")
            path = run_dir / "results" / str(item.get("file") or "")
            if not path.is_file():
                raise SystemExit(f"source result missing: {path}")
            if sha256(path) != item.get("sha256"):
                raise SystemExit(f"source result hash mismatch: {path.name}")

    print("THALARCH PUBLIC BENCHMARK MANIFEST VERIFIED")
    print(f"attestation_sha256: {actual_attestation}")
    print(f"result_count: {len(entries)}")
    print("source_run_verified: " + ("yes" if args.run_dir is not None else "not_requested"))


if __name__ == "__main__":
    main()
