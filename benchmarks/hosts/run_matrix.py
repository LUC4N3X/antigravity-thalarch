#!/usr/bin/env python3
"""Run one frozen LongBench task set across configured hosts.

The matrix does not guess vendor CLI flags. Each host command is supplied via the
environment variable declared in host_matrix.json, and the exact command template
hash is recorded without publishing its potentially sensitive contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LONG_RUNNER = REPO_ROOT / "benchmarks" / "long" / "run_longbench.py"
MATRIX_PATH = HERE / "host_matrix.json"


def template_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the same frozen LongBench set across configured hosts")
    parser.add_argument("--tasks-file", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--model-map", required=True, help='JSON object, e.g. {"antigravity":"model-a","codex":"model-b"}')
    parser.add_argument("--host", action="append", dest="hosts", choices=["antigravity", "codex", "claude"])
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--agent-timeout", type=int, default=1800)
    args = parser.parse_args()

    models = json.loads(args.model_map)
    if not isinstance(models, dict):
        raise SystemExit("--model-map must be a JSON object")
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    configs = matrix.get("hosts") if isinstance(matrix, dict) and isinstance(matrix.get("hosts"), dict) else {}
    hosts = args.hosts or ["antigravity", "codex", "claude"]
    prefix = args.run_prefix or datetime.now().strftime("%Y%m%d-%H%M%S-cross-host")

    records: list[dict[str, Any]] = []
    for host in hosts:
        config = configs.get(host) if isinstance(configs.get(host), dict) else {}
        env_name = str(config.get("command_env") or "")
        raw_command = os.environ.get(env_name, "") if env_name else ""
        model = str(models.get(host) or "")
        if not raw_command or not model:
            records.append({
                "host": host,
                "status": "SKIPPED_UNCONFIGURED",
                "command_env": env_name,
                "model_present": bool(model),
            })
            print(f"{host}: SKIPPED_UNCONFIGURED")
            continue

        run_id = f"{prefix}-{host}"
        cmd = [
            sys.executable,
            str(LONG_RUNNER),
            "--tasks-file", str(args.tasks_file),
            "--expected-sha256", args.expected_sha256,
            "--host", host,
            "--model", model,
            "--command-json", raw_command,
            "--agent-timeout", str(args.agent_timeout),
            "--run-id", run_id,
        ]
        proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        status = "COMPLETED" if proc.returncode == 0 else "FAILED"
        records.append({
            "host": host,
            "status": status,
            "run_id": run_id,
            "model": model,
            "command_template_sha256": template_hash(raw_command),
            "exit_code": proc.returncode,
        })
        print(f"{host}: {status} run_id={run_id}")
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)

    completed = [row for row in records if row["status"] == "COMPLETED"]
    failed = [row for row in records if row["status"] == "FAILED"]
    print("=== CROSS-HOST MATRIX ===")
    print(json.dumps({"hosts": records}, indent=2))
    if failed:
        raise SystemExit(2)
    if not completed:
        raise SystemExit("No host was configured; no cross-host benchmark was run")


if __name__ == "__main__":
    main()
