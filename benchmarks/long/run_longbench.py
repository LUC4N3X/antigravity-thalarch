#!/usr/bin/env python3
"""Long-horizon coding-agent benchmark with post-agent hidden tests.

Task definitions may remain outside the repository. Hidden files are injected
only after the agent process exits, so the model cannot inspect them during the
work phase. Grading distinguishes task failure from harness/host infrastructure
failure and enforces forbidden/protected-path boundaries.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
HOSTS = REPO_ROOT / "benchmarks" / "hosts"
sys.path.insert(0, str(HOSTS))
from host_command import command_template, render_command  # noqa: E402

RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results" / "long"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )


def init_repo(workspace: Path) -> None:
    proc = git("init", "-q", cwd=workspace)
    if proc.returncode != 0:
        raise RuntimeError("git init failed")
    git("config", "user.email", "longbench@example.invalid", cwd=workspace)
    git("config", "user.name", "Thalarch LongBench", cwd=workspace)
    git("add", "--all", cwd=workspace)
    proc = git("commit", "-q", "-m", "longbench fixture", cwd=workspace)
    if proc.returncode != 0:
        raise RuntimeError(f"git fixture commit failed: {proc.stderr.strip()}")


def write_files(root: Path, files: dict[str, Any]) -> None:
    for rel, content in files.items():
        rel_path = Path(str(rel))
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"unsafe fixture path: {rel}")
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")


def changed_paths(workspace: Path) -> list[str]:
    proc = git("status", "--porcelain=v1", "-z", cwd=workspace)
    if proc.returncode != 0:
        raise RuntimeError(f"git status failed: {proc.stderr.strip()}")
    paths: list[str] = []
    chunks = proc.stdout.split("\0")
    for chunk in chunks:
        if not chunk:
            continue
        text = chunk[3:] if len(chunk) >= 3 else chunk
        if " -> " in text:
            text = text.split(" -> ", 1)[1]
        paths.append(text.replace("\\", "/"))
    return sorted(set(paths))


def matches_any(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def expand_paths(workspace: Path, patterns: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in workspace.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(workspace).as_posix()
        if matches_any(rel, patterns):
            result[rel] = sha256_file(path)
    return result


def run_process(argv: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv, cwd=cwd, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=timeout,
        )
        return {
            "status": "completed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "wall_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "exit_code": None,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "wall_seconds": round(time.monotonic() - started, 3),
        }
    except OSError as exc:
        return {
            "status": "infra_error",
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "wall_seconds": round(time.monotonic() - started, 3),
        }


def validate_task(task: dict[str, Any]) -> None:
    required = {"id", "prompt", "fixture", "hidden_tests"}
    missing = required - set(task)
    if missing:
        raise ValueError("missing task fields: " + ", ".join(sorted(missing)))
    if not isinstance(task.get("fixture"), dict):
        raise ValueError("fixture must be an object")
    tests = task.get("hidden_tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("hidden_tests must be a non-empty list")
    for test in tests:
        if not isinstance(test, dict) or not isinstance(test.get("argv"), list):
            raise ValueError("each hidden test must contain argv array")
        if not all(isinstance(item, str) and item for item in test["argv"]):
            raise ValueError("hidden test argv must contain non-empty strings")


def run_task(
    task: dict[str, Any], *, host: str, model: str, command_json: str | None,
    agent_timeout: int, run_dir: Path,
) -> dict[str, Any]:
    validate_task(task)
    template = command_template(host, command_json)
    with tempfile.TemporaryDirectory(prefix=f"thalarch-long-{task['id']}-") as tmp:
        workspace = Path(tmp)
        write_files(workspace, task["fixture"])
        init_repo(workspace)

        protected_patterns = [str(x) for x in task.get("protected_paths", [])]
        forbidden_patterns = [str(x) for x in task.get("forbidden_paths", [])]
        protected_before = expand_paths(workspace, protected_patterns)

        prompt = str(task["prompt"]).strip()
        argv = render_command(template, prompt=prompt, workspace=workspace, model=model)
        agent = run_process(argv, workspace, agent_timeout)
        changed = changed_paths(workspace) if agent["status"] == "completed" else []
        forbidden_hits = [path for path in changed if matches_any(path, forbidden_patterns)]

        protected_after = expand_paths(workspace, protected_patterns)
        protected_regressions = sorted(
            path for path in set(protected_before) | set(protected_after)
            if protected_before.get(path) != protected_after.get(path)
        )

        # Hidden material appears only after agent execution and boundary capture.
        hidden_files = task.get("hidden_files") if isinstance(task.get("hidden_files"), dict) else {}
        for rel in hidden_files:
            if (workspace / rel).exists():
                raise ValueError(f"hidden file collides with agent-visible workspace path: {rel}")
        write_files(workspace, hidden_files)

        test_rows: list[dict[str, Any]] = []
        infra_error = agent["status"] == "infra_error"
        for index, test in enumerate(task["hidden_tests"], start=1):
            timeout = int(test.get("timeout", 120))
            test_result = run_process([str(x) for x in test["argv"]], workspace, timeout)
            if test_result["status"] == "infra_error":
                infra_error = True
            command_hash = sha256_bytes(json.dumps(test["argv"], separators=(",", ":")).encode())
            test_rows.append({
                "index": index,
                "command_sha256": command_hash,
                "status": test_result["status"],
                "exit_code": test_result["exit_code"],
                "wall_seconds": test_result["wall_seconds"],
            })

        tests_pass = all(row["status"] == "completed" and row["exit_code"] == 0 for row in test_rows)
        agent_completed = agent["status"] == "completed" and agent["exit_code"] == 0
        passed = agent_completed and tests_pass and not forbidden_hits and not protected_regressions and not infra_error

        raw_dir = run_dir / "raw" / host
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_stem = str(task["id"])
        (raw_dir / f"{raw_stem}.agent.stdout.txt").write_text(agent["stdout"], encoding="utf-8")
        (raw_dir / f"{raw_stem}.agent.stderr.txt").write_text(agent["stderr"], encoding="utf-8")

        result = {
            "schema_version": 1,
            "task_id": task["id"],
            "host": host,
            "model": model,
            "task_status": "PASS" if passed else "FAIL",
            "infra_status": "ERROR" if infra_error else "OK",
            "agent_status": agent["status"],
            "agent_exit_code": agent["exit_code"],
            "agent_wall_seconds": agent["wall_seconds"],
            "hidden_tests": test_rows,
            "changed_paths": changed,
            "forbidden_path_violations": forbidden_hits,
            "protected_path_regressions": protected_regressions,
            "hidden_files_count": len(hidden_files),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        return result


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run long-horizon tasks with post-agent hidden tests")
    parser.add_argument("--tasks-file", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--host", choices=["antigravity", "codex", "claude"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--command-json", default=None)
    parser.add_argument("--agent-timeout", type=int, default=1800)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    tasks_file = args.tasks_file.expanduser().resolve()
    if not tasks_file.is_file():
        raise SystemExit(f"tasks file not found: {tasks_file}")
    actual_sha = file_hash(tasks_file)
    if actual_sha.lower() != args.expected_sha256.strip().lower():
        raise SystemExit(f"task-set hash mismatch: expected {args.expected_sha256}, got {actual_sha}")
    payload = json.loads(tasks_file.read_text(encoding="utf-8"))
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, list) or not tasks:
        raise SystemExit("tasks file must contain a non-empty tasks array")

    run_dir = RESULTS_ROOT / args.run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SystemExit("run-id already contains artifacts")
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "run_id": args.run_id,
        "host": args.host,
        "model": args.model,
        "tasks_sha256": actual_sha,
        "task_count": len(tasks),
        "benchmark_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False
        ).stdout.strip() or "unknown",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    results: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise SystemExit("each task must be an object")
        row = run_task(
            task, host=args.host, model=args.model, command_json=args.command_json,
            agent_timeout=args.agent_timeout, run_dir=run_dir,
        )
        results.append(row)
        out = run_dir / "results" / f"{task['id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        print(
            f"{task['id']} {row['task_status']} infra={row['infra_status']} "
            f"hidden={sum(t['exit_code'] == 0 for t in row['hidden_tests'])}/{len(row['hidden_tests'])} "
            f"forbidden={len(row['forbidden_path_violations'])} protected={len(row['protected_path_regressions'])}"
        )

    valid = [row for row in results if row["infra_status"] == "OK"]
    summary = {
        "total": len(results),
        "valid": len(valid),
        "infra_errors": len(results) - len(valid),
        "task_pass_percent": round(100 * sum(row["task_status"] == "PASS" for row in valid) / len(valid), 1) if valid else None,
        "forbidden_path_violations": sum(len(row["forbidden_path_violations"]) for row in valid),
        "protected_path_regressions": sum(len(row["protected_path_regressions"]) for row in valid),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("=== LONGBENCH SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"Artifacts: {run_dir}")


if __name__ == "__main__":
    main()
