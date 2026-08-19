#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import run_antigravity as runner
import structured_output
from plugin_integrity import format_mismatch, verify_plugin_tree

HERE = Path(__file__).resolve().parent
BENCH_ROOT = HERE.parent
REPO_ROOT = BENCH_ROOT.parent


# The low-level runner remains available for debugging, but serious paired runs install the hardened
# stream-json isolator. Include every behavior-bearing benchmark component in the paired fingerprint.
structured_output.install_into(runner)


def paired_protocol_fingerprint() -> str:
    digest = hashlib.sha256()
    paths = [
        runner.CASES_PATH,
        runner.SCHEMA_PATH,
        runner.JUDGE_PATH,
        Path(runner.__file__).resolve(),
        Path(structured_output.__file__).resolve(),
        Path(__file__).resolve(),
    ]
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


runner.protocol_fingerprint = paired_protocol_fingerprint


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


def annotate_integrity(path: Path, integrity: dict[str, Any]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["plugin_match_verified"] = bool(integrity.get("match"))
    payload["plugin_source_fingerprint"] = integrity.get("source_fingerprint")
    payload["plugin_staged_fingerprint"] = integrity.get("staged_fingerprint")
    payload["plugin_staged_root"] = integrity.get("staged_root")
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def format_duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "?"
    total = int(round(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def result_path(run_dir: Path, case_id: str, phase: str, trial: int) -> Path:
    return run_dir / "results" / f"{case_id}.{phase}.r{trial:02d}.json"


def existing_result_matches(
    path: Path,
    *,
    case: dict[str, Any],
    phase: str,
    trial: int,
    manifest: dict[str, Any],
    integrity: dict[str, Any],
) -> tuple[bool, float | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False, None

    expected = {
        "case_id": case["id"],
        "trial": trial,
        "requested_model": manifest["requested_model"],
        "effort": manifest["effort"],
        "protocol_revision": manifest["protocol_revision"],
        "protocol_fingerprint": manifest["protocol_fingerprint"],
        "benchmark_revision": manifest["benchmark_revision"],
        "agy_version": manifest["agy_version"],
        "thalarch": phase == "thalarch",
        "thalarch_activation": "slash-skill:thalarch-mode" if phase == "thalarch" else "native-default-agent",
        "plugin_match_verified": True,
        "plugin_source_fingerprint": integrity.get("source_fingerprint"),
        "plugin_staged_fingerprint": integrity.get("staged_fingerprint"),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        return False, None

    wall = payload.get("cost", {}).get("wall_seconds")
    return True, float(wall) if isinstance(wall, (int, float)) else None


def score_results(run_dir: Path, *, heading: str = "=== SCORE ===") -> int:
    paths = sorted((run_dir / "results").glob("*.json"))
    if not paths:
        return 0
    print(f"\n{heading}")
    proc = subprocess.run(
        [sys.executable, str(BENCH_ROOT / "score_run.py"), *[str(path) for path in paths]],
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
    return proc.returncode


def resume_command(args: argparse.Namespace, run_id: str) -> str:
    parts = [
        "python .\\benchmarks\\quick\\run_pair.py",
        f'--model "{args.model}"',
        f"--effort {args.effort}" if args.effort else "",
        f"--repeat {args.repeat}",
        f'--run-id "{run_id}"',
        "--resume",
    ]
    for case_id in args.cases or []:
        parts.append(f"--case {case_id}")
    return " `\n    ".join(part for part in parts if part)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run counterbalanced native-vs-Thalarch Antigravity benchmark trials"
    )
    parser.add_argument("--model", required=True, help="Exact Antigravity model id; required for paired integrity")
    parser.add_argument("--effort", choices=["low", "medium", "high"], help="Optional pinned CLI reasoning effort")
    parser.add_argument("--repeat", type=int, default=3, help="Matched trials per case; default 3")
    parser.add_argument("--case", action="append", dest="cases", help="Run only this case id; repeatable")
    parser.add_argument("--run-id", default=None, help="Optional run id; defaults to current timestamp")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse already completed matching results in this run-id; requires an unchanged manifest/plugin",
    )
    args = parser.parse_args()

    if not 1 <= args.repeat <= 20:
        raise SystemExit("--repeat must be between 1 and 20")
    if args.resume and not args.run_id:
        raise SystemExit("--resume requires --run-id so the exact interrupted run is explicit")

    run_validator()
    agy = runner.ensure_agy()

    plugin_integrity = verify_plugin_tree()
    if not plugin_integrity.get("match"):
        print("\nBENCHMARK INFRA_ERROR")
        print("The staged Antigravity CLI copy of thalarch-mode does not exactly match this checkout.")
        print(format_mismatch(plugin_integrity))
        print("Re-stage the local plugin from this checkout before benchmarking.")
        print("No model run was started and no hallucination score was recorded.")
        raise SystemExit(2)

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

    manifest.update({
        "plugin_match_verified": True,
        "plugin_source_fingerprint": plugin_integrity.get("source_fingerprint"),
        "plugin_staged_fingerprint": plugin_integrity.get("staged_fingerprint"),
        "plugin_staged_root": plugin_integrity.get("staged_root"),
        "plugin_behavior_file_count": plugin_integrity.get("source_file_count"),
    })
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    suite = runner.load_json(runner.CASES_PATH)
    cases: list[dict[str, Any]] = suite["cases"]
    if args.cases:
        wanted = set(args.cases)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise SystemExit(f"Unknown case id(s): {', '.join(sorted(missing))}")

    total_steps = len(cases) * args.repeat * 2
    completed_steps = 0
    observed_seconds: list[float] = []

    print()
    print("=== THALARCH PAIRED QUICK BENCHMARK ===")
    print(f"run_id: {run_id}")
    print(f"protocol: {runner.PROTOCOL_REVISION}")
    print(f"fingerprint: {manifest['protocol_fingerprint'][:12]}")
    print(f"plugin fingerprint: {str(plugin_integrity['source_fingerprint'])[:12]} MATCH")
    print(f"plugin staged path: {plugin_integrity.get('staged_root')}")
    print(f"model: {args.model}")
    print(f"effort: {args.effort or 'default'}")
    print(f"cases: {len(cases)}")
    print(f"trials_per_case: {args.repeat}")
    print("order: counterbalanced per case/trial")
    print(f"resume: {'enabled' if args.resume else 'disabled'}")
    print()

    started_all = time.monotonic()
    try:
        for trial in range(1, args.repeat + 1):
            for case_index, case in enumerate(cases):
                native_first = (trial + case_index) % 2 == 1
                phases = ("native", "thalarch") if native_first else ("thalarch", "native")
                for phase in phases:
                    path = result_path(run_dir, case["id"], phase, trial)
                    if args.resume and path.is_file():
                        matches, wall = existing_result_matches(
                            path,
                            case=case,
                            phase=phase,
                            trial=trial,
                            manifest=manifest,
                            integrity=plugin_integrity,
                        )
                        if not matches:
                            raise runner.BenchmarkInfraError(
                                f"Resume refused for {path.name}: existing result does not match the current "
                                "manifest/plugin integrity. Start a new run-id instead of mixing evidence."
                            )
                        completed_steps += 1
                        if wall is not None:
                            observed_seconds.append(wall)
                        remaining = total_steps - completed_steps
                        avg_step = sum(observed_seconds) / len(observed_seconds) if observed_seconds else None
                        eta = avg_step * remaining if avg_step is not None else None
                        print(
                            f"[{completed_steps:02d}/{total_steps:02d}] {case['id']} r{trial:02d} {phase:8s}: "
                            f"RESUME-SKIP | ETA ~{format_duration(eta)}"
                        )
                        continue

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
                    annotate_integrity(path, plugin_integrity)
                    completed_steps += 1
                    observed_seconds.append(float(row["elapsed"]))
                    status = "PASS" if row["passed"] else "FAIL"
                    remaining = total_steps - completed_steps
                    avg_step = sum(observed_seconds) / len(observed_seconds)
                    eta = avg_step * remaining
                    elapsed_total = time.monotonic() - started_all
                    print(
                        f"[{completed_steps:02d}/{total_steps:02d}] {case['id']} r{trial:02d} {phase:8s}: {status} | "
                        f"{row['elapsed']:.1f}s | hallucinations={len(row['incidents'])} | "
                        f"elapsed {format_duration(elapsed_total)} | ETA ~{format_duration(eta)}"
                    )
                    for problem in row["problems"]:
                        print(f"  - {problem}")
    except runner.BenchmarkInfraError as exc:
        print("\nBENCHMARK INFRA_ERROR")
        print(str(exc))
        print("No hallucination score was recorded for this infrastructure failure.")
        score_results(run_dir, heading="=== PARTIAL SCORE (NOT PUBLISHABLE) ===")
        print("\nResume this exact unchanged run without repeating completed results:")
        print(resume_command(args, run_id))
        raise SystemExit(2)

    rc = score_results(run_dir)
    if rc != 0:
        raise SystemExit(rc)

    print(f"\nArtifacts: {run_dir}")


if __name__ == "__main__":
    main()
