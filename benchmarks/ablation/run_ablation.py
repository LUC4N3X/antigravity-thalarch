#!/usr/bin/env python3
"""Four-arm Thalarch ablation benchmark without changing the Quick protocol.

Arms:
- native: plugin disabled, no Thalarch skill activation
- skills_only: plugin enabled with every hook group disabled, `/thalarch-mode` activated
- gates_only: full plugin hooks enabled, no `/thalarch-mode` activation
- full: full plugin enabled and `/thalarch-mode` activated

The runner re-stages the exact source plugin when it exits, including after errors.
Ablation artifacts carry their own harness and plugin-variant fingerprints and are
never mixed with publishable Quick Protocol 4 pair results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

QUICK = Path(__file__).resolve().parents[1] / "quick"
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(QUICK))

import run_antigravity as quick  # noqa: E402
import structured_output  # noqa: E402
from judge import grade_case  # noqa: E402
from plugin_integrity import behavior_files, fingerprint  # noqa: E402

structured_output.install_into(quick)

ARMS = ("native", "skills_only", "gates_only", "full")
RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results" / "ablation"
SOURCE_PLUGIN = REPO_ROOT / "thalarch-mode"


def harness_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in [Path(__file__).resolve(), quick.CASES_PATH, quick.SCHEMA_PATH, quick.JUDGE_PATH]:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def install_plugin(agy: str, source: Path) -> None:
    quick.run_text([agy, "plugin", "uninstall", "thalarch-mode"])
    proc = quick.run_text([agy, "plugin", "install", str(source)])
    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "no CLI diagnostic").strip()
        raise quick.BenchmarkInfraError(f"Could not stage ablation plugin from {source}.\n{details}")


def set_all_hooks_enabled(plugin: Path, enabled: bool) -> None:
    path = plugin / "hooks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise quick.BenchmarkInfraError("hooks.json is not an object")
    for value in payload.values():
        if isinstance(value, dict) and "enabled" in value:
            value["enabled"] = enabled
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def stage_arm(agy: str, arm: str, scratch: Path) -> dict[str, Any]:
    if arm == "native":
        install_plugin(agy, SOURCE_PLUGIN)
        quick.set_thalarch_plugin_state(agy, enabled=False)
        files = behavior_files(SOURCE_PLUGIN)
        return {"plugin_fingerprint": fingerprint(files), "variant": "source-disabled"}

    if arm == "skills_only":
        variant = scratch / "thalarch-mode"
        shutil.copytree(SOURCE_PLUGIN, variant)
        set_all_hooks_enabled(variant, False)
        install_plugin(agy, variant)
        quick.set_thalarch_plugin_state(agy, enabled=True)
        files = behavior_files(variant)
        return {"plugin_fingerprint": fingerprint(files), "variant": "all-hooks-disabled"}

    install_plugin(agy, SOURCE_PLUGIN)
    quick.set_thalarch_plugin_state(agy, enabled=True)
    files = behavior_files(SOURCE_PLUGIN)
    return {
        "plugin_fingerprint": fingerprint(files),
        "variant": "source-hooks-no-skill" if arm == "gates_only" else "source-full",
    }


def prompt_for(case: dict[str, Any], arm: str) -> str:
    prompt = case["prompt"].strip()
    common = (
        "\n\nABLATION BENCHMARK CONTRACT:\n"
        "- Work read-only. Do not edit files, run destructive/external actions, create commits, push, or open PRs.\n"
        "- Inspect only the active benchmark workspace.\n"
        "- Inspect repository files only with list_dir and view_file; do not use grep_search, run_command, browser, web, MCP, or external tools.\n"
        "- `conclusion` is the verdict on the user's main factual proposition.\n"
        "- Every material factual assertion in `answer` must also appear in `claims`.\n"
        "- Return only the JSON object required by the supplied schema.\n"
        f"- Set case_id exactly to {case['id']}.\n"
    )
    if arm in {"skills_only", "full"}:
        return "/thalarch-mode\n\n" + prompt + common
    return prompt + common


def run_case(
    agy: str,
    case: dict[str, Any],
    arm: str,
    trial: int,
    model: str,
    effort: str | None,
    run_dir: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"thalarch-ab-{case['id'].lower()}-{arm}-") as tmp:
        workspace = Path(tmp)
        quick.write_fixture(case, workspace)
        schema_inline = json.dumps(quick.load_json(quick.SCHEMA_PATH), separators=(",", ":"))
        cmd = [
            agy,
            "-p",
            prompt_for(case, arm),
            f"--add-dir={workspace}",
            "--mode=plan",
            "--output-format=stream-json",
            f"--json-schema={schema_inline}",
            f"--model={model}",
        ]
        if effort:
            cmd.append(f"--effort={effort}")
        started = time.monotonic()
        proc = quick.run_text(cmd, cwd=workspace, env=quick.build_cli_env())
        elapsed = time.monotonic() - started

        raw_dir = run_dir / "raw" / arm
        raw_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{case['id']}.r{trial:02d}"
        stdout_path = raw_dir / f"{stem}.ndjson"
        stderr_path = raw_dir / f"{stem}.stderr.txt"
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise quick.BenchmarkInfraError(
                f"{case['id']} {arm} r{trial:02d}: CLI exit {proc.returncode}; raw={stdout_path}"
            )
        events = quick.parse_stream(proc.stdout)
        structured = quick.extract_result(events, proc.stdout)
        if structured is None:
            raise quick.BenchmarkInfraError(
                f"{case['id']} {arm} r{trial:02d}: no schema-conformant result; raw={stdout_path}"
            )
        passed, incidents, problems = grade_case(case, structured)
        result = {
            "case_id": case["id"],
            "trial": trial,
            "arm": arm,
            "host": "antigravity",
            "requested_model": model,
            "observed_model": quick.extract_model(events),
            "effort": effort or "default",
            "task_status": "PASS" if passed else "FAIL",
            "hallucinations": incidents,
            "problems": problems,
            "wall_seconds": round(elapsed, 3),
            "activation": "slash-skill:thalarch-mode" if arm in {"skills_only", "full"} else "native-default-agent",
            "hooks_expected": arm in {"gates_only", "full"},
            "plugin_fingerprint": manifest["arms"][arm]["plugin_fingerprint"],
            "harness_fingerprint": manifest["harness_fingerprint"],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        out = run_dir / "results" / f"{case['id']}.{arm}.r{trial:02d}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for arm in ARMS:
        rows = [row for row in results if row["arm"] == arm]
        n = len(rows)
        passes = sum(row["task_status"] == "PASS" for row in rows)
        hallucinations = sum(len(row["hallucinations"]) for row in rows)
        summary[arm] = {
            "n": n,
            "task_pass_percent": round(100 * passes / n, 1) if n else None,
            "hallucinations": hallucinations,
            "avg_wall_seconds": round(sum(row["wall_seconds"] for row in rows) / n, 3) if n else None,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run four-arm Thalarch ablation benchmark")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", choices=["low", "medium", "high"])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 20:
        raise SystemExit("--repeat must be between 1 and 20")

    agy = quick.ensure_agy()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S-ablation")
    run_dir = RESULTS_ROOT / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SystemExit("Ablation run-id already contains artifacts; use a new run-id")
    run_dir.mkdir(parents=True, exist_ok=True)

    suite = quick.load_json(quick.CASES_PATH)
    cases = list(suite["cases"])
    if args.cases:
        wanted = set(args.cases)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise SystemExit("Unknown case id(s): " + ", ".join(sorted(missing)))

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "model": args.model,
        "effort": args.effort or "default",
        "repeat": args.repeat,
        "cases": [case["id"] for case in cases],
        "harness_fingerprint": harness_fingerprint(),
        "benchmark_revision": quick.git_revision(),
        "agy_version": quick.cli_version(agy),
        "arms": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    results: list[dict[str, Any]] = []

    try:
        for trial in range(1, args.repeat + 1):
            for case_index, case in enumerate(cases):
                order = list(ARMS)
                rotate = (trial + case_index) % len(order)
                order = order[rotate:] + order[:rotate]
                for arm in order:
                    with tempfile.TemporaryDirectory(prefix=f"thalarch-ab-stage-{arm}-") as stage_tmp:
                        arm_meta = stage_arm(agy, arm, Path(stage_tmp))
                        previous = manifest["arms"].get(arm)
                        if previous and previous != arm_meta:
                            raise quick.BenchmarkInfraError(f"Ablation arm fingerprint drifted within run: {arm}")
                        manifest["arms"][arm] = arm_meta
                        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                        row = run_case(agy, case, arm, trial, args.model, args.effort, run_dir, manifest)
                        results.append(row)
                        print(
                            f"{case['id']} r{trial:02d} {arm:11s} "
                            f"{row['task_status']} hallucinations={len(row['hallucinations'])} {row['wall_seconds']:.1f}s"
                        )
    except quick.BenchmarkInfraError as exc:
        print("ABLATION INFRA_ERROR")
        print(str(exc))
        raise SystemExit(2)
    finally:
        try:
            install_plugin(agy, SOURCE_PLUGIN)
            quick.set_thalarch_plugin_state(agy, enabled=True)
        except Exception as exc:
            print(f"WARNING: could not restore exact source plugin automatically: {exc}", file=sys.stderr)

    summary = summarize(results)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n=== ABLATION SUMMARY ===")
    for arm in ARMS:
        row = summary[arm]
        print(
            f"{arm:11s} n={row['n']} pass={row['task_pass_percent']}% "
            f"hallucinations={row['hallucinations']} avg={row['avg_wall_seconds']}s"
        )
    print(f"Artifacts: {run_dir}")


if __name__ == "__main__":
    main()
