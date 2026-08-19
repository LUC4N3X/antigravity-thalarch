#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import run_antigravity as runner

HERE = Path(__file__).resolve().parent
BENCH_ROOT = HERE.parent
REPO_ROOT = BENCH_ROOT.parent


def run_validator() -> None:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "validate_benchmarks.py"), str(REPO_ROOT)],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="")
        raise SystemExit("Benchmark self-validation failed; paired run was not started.")
    print(proc.stdout, end="")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run counterbalanced native-vs-Thalarch Antigravity benchmark trials"
    )
    parser.add_argument("--model", required=True, help="Exact Antigravity model id; required for paired integrity")
    parser.add_argument("--effort", choices=["low", "medium", "high"], help="Optional pinned CLI reasoning effort")
    parser.add_argument("--repeat", type=int, default=3, help="Matched trials per case; default 3")
    parser.add_argument("--case", action="append", dest="cases", help="Run only this case id; repeatable")
    parser.add_argument("--run-id", default=None, help="Optional run id; defaults to current timestamp")
    args = parser.parse_args()

    if not 1 <= args.repeat <= 20:
        raise SystemExit("--repeat must be between 1 and 20")

    run_validator()
    agy = runner.ensure_agy()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runner.RESULTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        manifest = runner.ensure_run_manifest(
            run_dir,
            agy=agy,
            model=args.model,
            effort=args.effort,
        )
    except runner.BenchmarkInfraError as exc:
        print("BENCHMARK INFRA_ERROR")
        print(str(exc))
        raise SystemExit(2)

    suite = runner.load_json(runner.CASES_PATH)
    cases: list[dict[str, Any]] = suite["cases"]
    if args.cases:
        wanted = set(args.cases)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise SystemExit(f"Unknown case id(s): {', '.join(sorted(missing))}")

    print()
    print("=== THALARCH PAIRED QUICK BENCHMARK ===")
    print(f"run_id: {run_id}")
    print(f"protocol: {runner.PROTOCOL_REVISION}")
    print(f"fingerprint: {manifest['protocol_fingerprint'][:12]}")
    print(f"model: {args.model}")
    print(f"effort: {args.effort or 'default'}")
    print(f"cases: {len(cases)}")
    print(f"trials_per_case: {args.repeat}")
    print("order: counterbalanced per case/trial")
    print()

    try:
        for trial in range(1, args.repeat + 1):
            for case_index, case in enumerate(cases):
                native_first = (trial + case_index) % 2 == 1
                phases = ("native", "thalarch") if native_first else ("thalarch", "native")
                for phase in phases:
                    runner.set_thalarch_plugin_state(agy, enabled=phase == "thalarch")
                    row = runner.run_case(
                        agy,
                        case,
                        phase,
                        trial,
                        args.model,
                        args.effort,
                        run_dir,
                        manifest,
                    )
                    status = "PASS" if row["passed"] else "FAIL"
                    print(
                        f"{case['id']} r{trial:02d} {phase:8s}: {status} | "
                        f"{row['elapsed']:.1f}s | hallucinations={len(row['incidents'])}"
                    )
                    for problem in row["problems"]:
                        print(f"  - {problem}")
    except runner.BenchmarkInfraError as exc:
        print("\nBENCHMARK INFRA_ERROR")
        print(str(exc))
        print("No hallucination score was recorded for this infrastructure failure.")
        raise SystemExit(2)

    result_paths = sorted((run_dir / "results").glob("*.json"))
    if not result_paths:
        raise SystemExit("No result JSON files were produced.")

    print("\n=== SCORE ===")
    proc = subprocess.run(
        [sys.executable, str(BENCH_ROOT / "score_run.py"), *[str(path) for path in result_paths]],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)

    print(f"\nArtifacts: {run_dir}")


if __name__ == "__main__":
    main()
