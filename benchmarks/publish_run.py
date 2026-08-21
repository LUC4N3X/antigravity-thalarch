#!/usr/bin/env python3
"""Create a sanitized, hash-verifiable public manifest from a benchmark run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_hash(payload: dict[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("attestation_sha256", None)
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return digest_bytes(raw)


def result_entry(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    hallucinations = data.get("hallucinations") if isinstance(data.get("hallucinations"), list) else []
    cost = data.get("cost") if isinstance(data.get("cost"), dict) else {}
    mode = data.get("arm")
    if not mode:
        mode = "thalarch" if data.get("thalarch") is True else "native"
    return {
        "file": path.name,
        "sha256": digest_file(path),
        "case_id": data.get("case_id"),
        "trial": data.get("trial"),
        "host": data.get("host"),
        "mode": mode,
        "task_status": data.get("task_status"),
        "hallucinations": len(hallucinations),
        "wall_seconds": cost.get("wall_seconds", data.get("wall_seconds")),
        "protocol_revision": data.get("protocol_revision"),
        "protocol_fingerprint": data.get("protocol_fingerprint", data.get("harness_fingerprint")),
        "plugin_fingerprint": data.get("plugin_source_fingerprint", data.get("plugin_fingerprint")),
    }


def aggregate(entries: list[dict[str, Any]]) -> dict[str, Any]:
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


def create_public_manifest(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"manifest.json not found in {run_dir}")
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    result_paths = sorted((run_dir / "results").glob("*.json"))
    if not result_paths:
        raise SystemExit(f"no result JSON files found in {run_dir / 'results'}")
    entries = [result_entry(path) for path in result_paths]
    public = {
        "schema_version": 1,
        "run_id": source.get("run_id", run_dir.name),
        "model": source.get("requested_model", source.get("model")),
        "effort": source.get("effort"),
        "protocol_revision": source.get("protocol_revision"),
        "protocol_fingerprint": source.get("protocol_fingerprint", source.get("harness_fingerprint")),
        "benchmark_revision": source.get("benchmark_revision"),
        "agy_version": source.get("agy_version"),
        "plugin_source_fingerprint": source.get("plugin_source_fingerprint"),
        "plugin_staged_fingerprint": source.get("plugin_staged_fingerprint"),
        "source_manifest_sha256": digest_file(manifest_path),
        "result_count": len(entries),
        "results": entries,
        "aggregate": aggregate(entries),
        "privacy": {
            "raw_transcripts_included": False,
            "local_absolute_paths_included": False,
            "result_files_included": False,
            "result_hashes_included": True,
        },
    }
    public["attestation_sha256"] = canonical_hash(public)
    return public


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a sanitized benchmark manifest")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    public = create_public_manifest(args.run_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"THALARCH PUBLIC BENCHMARK MANIFEST WRITTEN: {args.output}")
    print(f"attestation_sha256: {public['attestation_sha256']}")
    print(f"result_count: {public['result_count']}")


if __name__ == "__main__":
    main()
