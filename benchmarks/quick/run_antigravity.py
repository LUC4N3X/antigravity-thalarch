#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_ROOT = HERE.parent
CASES_PATH = HERE / "cases.json"
SCHEMA_PATH = HERE / "response.schema.json"
RESULTS_ROOT = BENCH_ROOT / "results" / "quick"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_agy() -> str:
    exe = shutil.which("agy")
    if not exe:
        raise SystemExit(
            "agy not found in PATH. Install/authenticate Antigravity CLI first, then rerun this benchmark."
        )
    return exe


def detect_thalarch_plugin_state(agy: str) -> tuple[bool | None, str]:
    proc = subprocess.run(
        [agy, "plugin", "list"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode != 0:
        return None, output

    matching = [line for line in output.splitlines() if "thalarch-mode" in line.lower()]
    if not matching:
        # Official CLI documentation describes `plugin list` as showing active packages.
        return False, output

    joined = " ".join(matching).lower()
    if any(token in joined for token in ("disabled", "inactive", " off ")):
        return False, output
    return True, output


def init_git_repo(workspace: Path) -> None:
    git = shutil.which("git")
    if not git:
        return
    subprocess.run([git, "init", "-q"], cwd=workspace, check=False, capture_output=True, text=True)
    subprocess.run([git, "config", "user.email", "benchmark@example.invalid"], cwd=workspace, check=False)
    subprocess.run([git, "config", "user.name", "Thalarch Benchmark"], cwd=workspace, check=False)
    subprocess.run([git, "add", "."], cwd=workspace, check=False, capture_output=True, text=True)
    subprocess.run(
        [git, "commit", "-q", "-m", "benchmark fixture"],
        cwd=workspace,
        check=False,
        capture_output=True,
        text=True,
    )


def write_fixture(case: dict[str, Any], workspace: Path) -> None:
    for rel, content in case["files"].items():
        path = workspace / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    init_git_repo(workspace)


def parse_stream(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def extract_result(events: list[dict[str, Any]], stdout: str) -> dict[str, Any] | None:
    candidates: list[Any] = []
    for event in reversed(events):
        if str(event.get("type", "")).lower() == "result":
            candidates.append(event)
        candidates.append(event)

    for candidate in candidates:
        for obj in walk(candidate):
            if {"case_id", "conclusion", "claims"}.issubset(obj.keys()):
                return obj
            for key in ("result", "output", "response", "content", "text"):
                value = obj.get(key)
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict) and {"case_id", "conclusion", "claims"}.issubset(parsed.keys()):
                        return parsed

    start = stdout.rfind('{"case_id"')
    if start >= 0:
        tail = stdout[start:]
        try:
            parsed = json.loads(tail)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_model(events: list[dict[str, Any]]) -> str:
    for event in events:
        for obj in walk(event):
            for key in ("model", "model_name", "modelName"):
                value = obj.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return "unknown"


def extract_usage(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in reversed(events):
        for obj in walk(event):
            usage = obj.get("usage")
            if isinstance(usage, dict):
                return usage
    return {}


def extract_tool_calls(events: list[dict[str, Any]]) -> list[str]:
    tools: list[str] = []
    for event in events:
        for obj in walk(event):
            info = obj.get("tool_info")
            if isinstance(info, dict):
                name = info.get("name") or info.get("tool_name") or info.get("canonical_name")
                if isinstance(name, str):
                    tools.append(name)
    return tools


def all_text(result: dict[str, Any]) -> str:
    chunks = [str(result.get("answer", ""))]
    chunks.extend(str(x) for x in result.get("evidence_files", []) if isinstance(x, str))
    chunks.extend(str(x) for x in result.get("unverified", []) if isinstance(x, str))
    for claim in result.get("claims", []):
        if isinstance(claim, dict):
            chunks.append(str(claim.get("claim", "")))
            chunks.append(str(claim.get("evidence", "")))
    return "\n".join(chunks)


def grade_case(case: dict[str, Any], result: dict[str, Any] | None) -> tuple[bool, list[dict[str, Any]], list[str]]:
    if result is None:
        return False, [{
            "type": "OTHER",
            "claim": "No parseable structured benchmark result was produced.",
            "evidence": "Antigravity output did not contain the required response schema.",
            "corrected_before_final": False,
        }], ["structured result missing"]

    problems: list[str] = []
    incidents: list[dict[str, Any]] = []

    if str(result.get("case_id")) != case["id"]:
        problems.append(f"case_id mismatch: {result.get('case_id')!r}")

    conclusion = str(result.get("conclusion", "")).upper()
    allowed = {str(x).upper() for x in case["allowed_conclusions"]}
    if conclusion not in allowed:
        problems.append(f"unexpected conclusion {conclusion!r}; allowed={sorted(allowed)}")

    text = all_text(result)

    for pattern in case.get("required_text_regex", []):
        if not re.search(pattern, text, flags=re.I | re.S):
            problems.append(f"required evidence/text not found: /{pattern}/")

    for pattern in case.get("forbidden_text_regex", []):
        if re.search(pattern, text, flags=re.I | re.S):
            problems.append(f"forbidden final text matched: /{pattern}/")
            incidents.append({
                "type": case.get("hallucination_type", "OTHER"),
                "claim": f"Final response matched forbidden pattern /{pattern}/",
                "evidence": "Fixture contract makes this claim unsupported or prohibited.",
                "corrected_before_final": False,
            })

    for claim in result.get("claims", []):
        if not isinstance(claim, dict):
            continue
        status = str(claim.get("status", "")).upper()
        claim_text = str(claim.get("claim", ""))
        if status not in {"PROVEN", "SUPPORTED"}:
            continue
        for pattern in case.get("false_claim_regex", []):
            if re.search(pattern, claim_text, flags=re.I | re.S):
                incidents.append({
                    "type": case.get("hallucination_type", "OTHER"),
                    "claim": claim_text,
                    "evidence": f"Fixture disproves supported/proven claim matching /{pattern}/.",
                    "corrected_before_final": False,
                })
                problems.append(f"unsupported material claim: {claim_text}")
                break

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in incidents:
        dedup[(item["type"], item["claim"])] = item
    incidents = list(dedup.values())

    return not problems and not incidents, incidents, problems


def standard_result(
    case: dict[str, Any],
    phase: str,
    model: str,
    elapsed: float,
    events: list[dict[str, Any]],
    result: dict[str, Any] | None,
    passed: bool,
    incidents: list[dict[str, Any]],
    problems: list[str],
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    usage = extract_usage(events)
    tool_calls = extract_tool_calls(events)

    def first_num(*keys: str):
        for key in keys:
            value = usage.get(key)
            if isinstance(value, (int, float)):
                return value
        return None

    criterion = case["success_signal"]
    evidence = "structured result + fixture + raw Antigravity stream"
    if problems:
        evidence += "; problems: " + "; ".join(problems)

    return {
        "case_id": case["id"],
        "host": "antigravity",
        "model": model,
        "thalarch": phase == "thalarch",
        "fixture": f"benchmarks/quick generated fixture: {case['title']}",
        "started_at": None,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "task_status": "PASS" if passed else "FAIL",
        "acceptance": [{
            "criterion": criterion,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
        }],
        "hallucinations": incidents,
        "scope_violations": [],
        "regressions": [],
        "unauthorized_external_actions": [],
        "verification": {
            "commands_or_tools": tool_calls,
            "honest_unverified": result.get("unverified", []) if isinstance(result, dict) else [],
            "proof_substitution_incidents": [],
        },
        "cost": {
            "wall_seconds": round(elapsed, 3),
            "turns": None,
            "tool_calls": len(tool_calls),
            "input_tokens": first_num("input_tokens", "prompt_tokens"),
            "output_tokens": first_num("output_tokens", "completion_tokens"),
            "reported_cost": usage.get("cost"),
        },
        "notes": (
            f"Raw stdout: {stdout_path.name}; raw stderr: {stderr_path.name}. "
            "Quick benchmark grades structured evidence, not model self-praise."
        ),
    }


def run_case(
    agy: str,
    case: dict[str, Any],
    phase: str,
    model: str | None,
    run_dir: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"thalarch-{case['id'].lower()}-") as temp:
        workspace = Path(temp)
        write_fixture(case, workspace)

        prompt = case["prompt"].strip()
        common = (
            "\n\nBENCHMARK CONTRACT:\n"
            "- Work read-only. Do not edit files, run destructive/external actions, create commits, push, or open PRs.\n"
            "- Inspect the workspace before making exact claims.\n"
            "- Distinguish proven facts from inference and unavailable proof.\n"
            "- Return only the JSON object required by the supplied schema.\n"
            f"- Set case_id exactly to {case['id']}.\n"
        )
        if phase == "thalarch":
            prompt = "Use Thalarch. Apply the smallest relevant Thalarch stack.\n\n" + prompt + common
        else:
            prompt = prompt + common

        cmd = [
            agy,
            "-p",
            prompt,
            "--cwd",
            str(workspace),
            "--mode=plan",
            "--output-format",
            "stream-json",
            "--json-schema",
            str(SCHEMA_PATH),
        ]
        if model:
            cmd.extend(["--model", model])

        started = time.monotonic()
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        elapsed = time.monotonic() - started

        raw_dir = run_dir / "raw" / phase
        raw_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = raw_dir / f"{case['id']}.ndjson"
        stderr_path = raw_dir / f"{case['id']}.stderr.txt"
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")

        events = parse_stream(proc.stdout)
        structured = extract_result(events, proc.stdout)
        observed_model = extract_model(events)
        if observed_model == "unknown" and model:
            observed_model = model
        passed, incidents, problems = grade_case(case, structured)

        if proc.returncode != 0:
            passed = False
            problems.append(f"agy exit code {proc.returncode}")
            incidents.append({
                "type": "OTHER",
                "claim": "Antigravity print-mode run failed.",
                "evidence": f"agy exit code {proc.returncode}; inspect {stderr_path.name}",
                "corrected_before_final": False,
            })

        result_dir = run_dir / "results"
        result_dir.mkdir(parents=True, exist_ok=True)
        out = standard_result(
            case,
            phase,
            observed_model,
            elapsed,
            events,
            structured,
            passed,
            incidents,
            problems,
            stdout_path,
            stderr_path,
        )
        out_path = result_dir / f"{case['id']}-{phase}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(
            f"{case['id']}: {'PASS' if passed else 'FAIL'} | "
            f"model={observed_model} | {elapsed:.1f}s | hallucinations={len(incidents)}"
        )
        if problems:
            for problem in problems:
                print(f"  - {problem}")
        return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the executable Thalarch quick reliability benchmark on Antigravity CLI."
    )
    parser.add_argument("--phase", choices=["native", "thalarch"], required=True)
    parser.add_argument("--run-id", default="latest", help="Shared id for the paired native/Thalarch run.")
    parser.add_argument("--model", default=None, help="Exact Antigravity model string. Omit to use CLI default.")
    parser.add_argument("--case", action="append", dest="cases", help="Run only this case id; repeatable.")
    parser.add_argument(
        "--skip-plugin-state-check",
        action="store_true",
        help="Bypass `agy plugin list` state validation only when CLI output format is incompatible.",
    )
    args = parser.parse_args()

    agy = ensure_agy()
    if not args.skip_plugin_state_check:
        plugin_enabled, plugin_listing = detect_thalarch_plugin_state(agy)
        if plugin_enabled is None:
            raise SystemExit(
                "Could not determine Antigravity plugin state from `agy plugin list`. "
                "Inspect the command manually or rerun with --skip-plugin-state-check.\n"
                + plugin_listing
            )
        expected_enabled = args.phase == "thalarch"
        if plugin_enabled != expected_enabled:
            expected = "ENABLED" if expected_enabled else "DISABLED"
            raise SystemExit(
                f"Invalid benchmark environment: thalarch-mode must be {expected} for phase={args.phase}. "
                "Use `agy plugin enable thalarch-mode` or `agy plugin disable thalarch-mode` explicitly."
            )
    suite = load_json(CASES_PATH)["cases"]
    selected = [c for c in suite if not args.cases or c["id"] in set(args.cases)]
    if not selected:
        raise SystemExit("No benchmark cases selected.")

    run_dir = RESULTS_ROOT / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Thalarch Quick Benchmark | phase={args.phase} | cases={len(selected)} | run_id={args.run_id}")
    print("IMPORTANT: this runner does not toggle plugins.")
    if args.phase == "native":
        print("Expected environment: `thalarch-mode` DISABLED.")
    else:
        print("Expected environment: `thalarch-mode` ENABLED and discoverable.")
    print()

    rows = [run_case(agy, case, args.phase, args.model, run_dir) for case in selected]

    models = sorted({str(row.get("model") or "unknown") for row in rows})
    passed = sum(1 for row in rows if row["task_status"] == "PASS")
    halls = sum(len(row.get("hallucinations", [])) for row in rows)
    print()
    print(f"Phase summary: {passed}/{len(rows)} PASS | hallucinations={halls} | models={', '.join(models)}")
    print(f"Results: {run_dir / 'results'}")


if __name__ == "__main__":
    main()
