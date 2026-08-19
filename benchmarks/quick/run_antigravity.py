#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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


class BenchmarkInfraError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_text(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def build_cli_env() -> dict[str, str]:
    """Keep the benchmark self-contained while making Git-for-Windows grep discoverable."""
    env = os.environ.copy()
    path_value = env.get("PATH", "")
    if os.name != "nt" or shutil.which("grep", path=path_value):
        return env

    candidates: list[Path] = []
    git = shutil.which("git")
    if git:
        git_path = Path(git).resolve()
        # Typical Git for Windows layout: <root>/cmd/git.exe + <root>/usr/bin/grep.exe.
        root = git_path.parent.parent
        candidates.extend([root / "usr" / "bin", root / "mingw64" / "bin"])

    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = env.get(key)
        if not base:
            continue
        base_path = Path(base)
        candidates.extend([
            base_path / "Git" / "usr" / "bin",
            base_path / "Git" / "mingw64" / "bin",
        ])

    seen: set[str] = set()
    for candidate in candidates:
        marker = str(candidate).lower()
        if marker in seen:
            continue
        seen.add(marker)
        if (candidate / "grep.exe").is_file():
            env["PATH"] = str(candidate) + os.pathsep + path_value
            break
    return env


def ensure_agy() -> str:
    exe = shutil.which("agy") or shutil.which("agy.exe")
    if exe:
        return exe

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        for candidate in (
            Path(local_app_data) / "agy" / "bin" / "agy.exe",
            Path(local_app_data) / "agy" / "bin" / "agy",
        ):
            if candidate.is_file():
                return str(candidate)

    raise SystemExit(
        "Antigravity CLI (`agy`) was not found in PATH or the standard Windows install directory. "
        "Install/authenticate Antigravity CLI, open a fresh terminal, then rerun this benchmark."
    )


def set_thalarch_plugin_state(agy: str, enabled: bool) -> None:
    action = "enable" if enabled else "disable"
    proc = run_text([agy, "plugin", action, "thalarch-mode"])
    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "no CLI diagnostic").strip()
        raise BenchmarkInfraError(
            f"Could not {action} thalarch-mode (agy exit {proc.returncode}).\n{details}"
        )


def init_git_repo(workspace: Path) -> None:
    git = shutil.which("git")
    if not git:
        return
    run_text([git, "init", "-q"], cwd=workspace)
    run_text([git, "config", "user.email", "benchmark@example.invalid"], cwd=workspace)
    run_text([git, "config", "user.name", "Thalarch Benchmark"], cwd=workspace)
    run_text([git, "add", "."], cwd=workspace)
    run_text([git, "commit", "-q", "-m", "benchmark fixture"], cwd=workspace)


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
    for event in reversed(events):
        for obj in walk(event):
            if {"case_id", "conclusion", "claims"}.issubset(obj.keys()):
                return obj
            for key in ("result", "output", "response", "content", "text"):
                value = obj.get(key)
                if not isinstance(value, str):
                    continue
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict) and {"case_id", "conclusion", "claims"}.issubset(parsed.keys()):
                    return parsed

    start = stdout.rfind('{"case_id"')
    if start >= 0:
        try:
            parsed = json.loads(stdout[start:])
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
                if isinstance(value, dict):
                    for nested in ("id", "name", "display_name", "displayName"):
                        nested_value = value.get(nested)
                        if isinstance(nested_value, str) and nested_value.strip():
                            return nested_value.strip()
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


def grade_case(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[dict[str, Any]], list[str]]:
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
        if str(claim.get("status", "")).upper() not in {"PROVEN", "SUPPORTED"}:
            continue
        claim_text = str(claim.get("claim", ""))
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
    result: dict[str, Any],
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

    evidence = "structured result + deterministic fixture + raw Antigravity stream"
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
            "criterion": case["success_signal"],
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
        }],
        "hallucinations": incidents,
        "scope_violations": [],
        "regressions": [],
        "unauthorized_external_actions": [],
        "verification": {
            "commands_or_tools": tool_calls,
            "honest_unverified": result.get("unverified", []),
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
            "Infrastructure failures are never scored as model hallucinations."
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
            "- Inspect only the active benchmark workspace; never inspect CLI scratch, home, or other non-workspace paths.\n"
            "- For this quick suite, inspect repository files only with list_dir and view_file. "
            "Do not use grep_search, run_command, browser, web, MCP, or external tools.\n"
            "- Distinguish proven facts from inference and unavailable proof.\n"
            "- Return only the JSON object required by the supplied schema.\n"
            f"- Set case_id exactly to {case['id']}.\n"
        )
        if phase == "thalarch":
            prompt = "Use Thalarch. Apply the smallest relevant Thalarch stack.\n\n" + prompt + common
        else:
            prompt += common

        schema_inline = json.dumps(load_json(SCHEMA_PATH), separators=(",", ":"))
        cmd = [
            agy,
            "-p",
            prompt,
            f"--add-dir={workspace}",
            "--mode=plan",
            "--output-format=stream-json",
            f"--json-schema={schema_inline}",
        ]
        if model:
            cmd.append(f"--model={model}")

        started = time.monotonic()
        proc = run_text(cmd, cwd=workspace, env=build_cli_env())
        elapsed = time.monotonic() - started

        raw_dir = run_dir / "raw" / phase
        raw_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = raw_dir / f"{case['id']}.ndjson"
        stderr_path = raw_dir / f"{case['id']}.stderr.txt"
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")

        if proc.returncode != 0:
            diagnostic = (proc.stderr or proc.stdout or "no CLI diagnostic").strip()
            raise BenchmarkInfraError(
                f"{case['id']}: Antigravity CLI failed before a benchmark answer (exit {proc.returncode}).\n"
                f"stderr/stdout:\n{diagnostic}\n"
                f"raw stderr: {stderr_path}\nraw stdout: {stdout_path}"
            )

        events = parse_stream(proc.stdout)
        structured = extract_result(events, proc.stdout)
        if structured is None:
            raise BenchmarkInfraError(
                f"{case['id']}: Antigravity exited successfully but no schema-conformant structured result "
                f"could be parsed. This is an infrastructure/harness failure, not a hallucination.\n"
                f"raw stderr: {stderr_path}\nraw stdout: {stdout_path}"
            )

        observed_model = extract_model(events)
        if observed_model == "unknown" and model:
            observed_model = model
        passed, incidents, problems = grade_case(case, structured)

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
        (result_dir / f"{case['id']}-{phase}.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(
            f"{case['id']}: {'PASS' if passed else 'FAIL'} | "
            f"model={observed_model} | {elapsed:.1f}s | hallucinations={len(incidents)}"
        )
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
    args = parser.parse_args()

    agy = ensure_agy()
    run_dir = RESULTS_ROOT / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        set_thalarch_plugin_state(agy, enabled=args.phase == "thalarch")
    except BenchmarkInfraError as exc:
        print("BENCHMARK INFRA_ERROR")
        print(exc)
        raise SystemExit(2)

    suite = load_json(CASES_PATH)["cases"]
    requested = set(args.cases or [])
    selected = [case for case in suite if not requested or case["id"] in requested]
    if not selected:
        raise SystemExit("No benchmark cases selected.")

    print(f"Thalarch Quick Benchmark | phase={args.phase} | cases={len(selected)} | run_id={args.run_id}")
    print(f"Plugin state requested by runner: {'ENABLED' if args.phase == 'thalarch' else 'DISABLED'}")
    print("Workspace policy: active fixture only; list_dir/view_file read tools only.")
    print()

    rows: list[dict[str, Any]] = []
    for case in selected:
        try:
            rows.append(run_case(agy, case, args.phase, args.model, run_dir))
        except BenchmarkInfraError as exc:
            print("BENCHMARK INFRA_ERROR")
            print(exc)
            print("No hallucination score was recorded for this infrastructure failure.")
            raise SystemExit(2)

    models = sorted({str(row.get("model") or "unknown") for row in rows})
    passed = sum(1 for row in rows if row["task_status"] == "PASS")
    halls = sum(len(row.get("hallucinations", [])) for row in rows)
    print()
    print(f"Phase summary: {passed}/{len(rows)} PASS | hallucinations={halls} | models={', '.join(models)}")
    print(f"Results: {run_dir / 'results'}")


if __name__ == "__main__":
    main()
