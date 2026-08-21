#!/usr/bin/env python3
"""Run the paired Quick harness against a frozen external holdout case file.

The holdout file is intentionally external by default. Its expected SHA-256 must
be supplied so a run cannot silently change the hidden evaluation set. The
underlying paired runner, scorer, model/config pinning, staged-plugin integrity,
and resume guards remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
QUICK = REPO_ROOT / "benchmarks" / "quick"
sys.path.insert(0, str(QUICK))

import run_antigravity as quick  # noqa: E402
import run_pair  # noqa: E402

RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results" / "holdout"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except Exception:
        return False


def validate_cases(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("protocol_revision") != quick.PROTOCOL_REVISION:
        raise SystemExit(f"Holdout must use protocol_revision={quick.PROTOCOL_REVISION}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("Holdout must contain a non-empty cases array")
    ids: set[str] = set()
    required = {"id", "title", "prompt", "files", "success_signal"}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise SystemExit(f"cases[{index}] must be an object")
        missing = required - set(case)
        if missing:
            raise SystemExit(f"cases[{index}] missing fields: {', '.join(sorted(missing))}")
        case_id = str(case.get("id") or "")
        if not case_id or case_id in ids:
            raise SystemExit(f"duplicate/empty holdout case id: {case_id!r}")
        ids.add(case_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a SHA-locked external holdout through the paired Quick harness")
    parser.add_argument("--cases-file", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--allow-public-in-repo", action="store_true")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", choices=["low", "medium", "high"])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    cases_file = args.cases_file.expanduser().resolve()
    if not cases_file.is_file():
        raise SystemExit(f"Holdout case file not found: {cases_file}")
    if inside_repo(cases_file) and not args.allow_public_in_repo:
        raise SystemExit(
            "Refusing an in-repository holdout by default. Keep frozen holdout cases outside the checkout "
            "or pass --allow-public-in-repo for a development/public set."
        )
    actual = sha256(cases_file)
    expected = args.expected_sha256.strip().lower()
    if actual.lower() != expected:
        raise SystemExit(f"Frozen holdout hash mismatch: expected {expected}, got {actual}")
    validate_cases(cases_file)

    quick.CASES_PATH = cases_file
    quick.RESULTS_ROOT = RESULTS_ROOT
    run_pair.runner.CASES_PATH = cases_file
    run_pair.runner.RESULTS_ROOT = RESULTS_ROOT

    forwarded = [
        "run_pair.py",
        "--model", args.model,
        "--repeat", str(args.repeat),
        "--run-id", args.run_id,
    ]
    if args.effort:
        forwarded += ["--effort", args.effort]
    if args.resume:
        forwarded.append("--resume")
    for case_id in args.cases or []:
        forwarded += ["--case", case_id]

    print("=== THALARCH FROZEN HOLDOUT ===")
    print(f"cases_sha256: {actual}")
    print(f"cases_count: {len(json.loads(cases_file.read_text(encoding='utf-8'))['cases'])}")
    print("case contents: external/not copied into the repository")
    old_argv = sys.argv
    try:
        sys.argv = forwarded
        run_pair.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
