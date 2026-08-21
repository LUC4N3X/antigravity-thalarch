#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []
required = [
    root / "benchmarks" / "ablation" / "run_ablation.py",
    root / "benchmarks" / "holdout" / "run_holdout.py",
    root / "benchmarks" / "hosts" / "host_command.py",
    root / "benchmarks" / "hosts" / "host_matrix.json",
    root / "benchmarks" / "hosts" / "run_matrix.py",
    root / "benchmarks" / "long" / "run_longbench.py",
    root / "benchmarks" / "long" / "tasks.schema.json",
    root / "benchmarks" / "publish_run.py",
    root / "benchmarks" / "verify_published_run.py",
    root / "benchmarks" / "test_robustness_matrix.py",
]
for path in required:
    if not path.is_file():
        errors.append(f"missing robustness benchmark asset: {path.relative_to(root)}")
        continue
    if path.suffix == ".py":
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"syntax error in {path.relative_to(root)}: {exc}")
    if path.suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON in {path.relative_to(root)}: {exc}")

checks = {
    root / "benchmarks" / "ablation" / "run_ablation.py": [
        'ARMS = ("native", "skills_only", "gates_only", "full")',
        "set_all_hooks_enabled",
        "install_plugin(agy, SOURCE_PLUGIN)",
    ],
    root / "benchmarks" / "holdout" / "run_holdout.py": [
        "expected-sha256",
        "Refusing an in-repository holdout",
        "cases_sha256",
    ],
    root / "benchmarks" / "long" / "run_longbench.py": [
        "hidden_files",
        "forbidden_paths",
        "protected_paths",
        "infra_status",
        "command_sha256",
    ],
    root / "benchmarks" / "publish_run.py": [
        "raw_transcripts_included",
        "attestation_sha256",
        "result_hashes_included",
    ],
    root / "benchmarks" / "hosts" / "run_matrix.py": [
        "command_env",
        "SKIPPED_UNCONFIGURED",
        "command_template_sha256",
    ],
}
for path, terms in checks.items():
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    for term in terms:
        if term not in text:
            errors.append(f"{path.relative_to(root)} missing robustness invariant: {term}")

if errors:
    print("THALARCH ROBUSTNESS-MATRIX VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

proc = subprocess.run(
    [sys.executable, "-m", "unittest", "benchmarks/test_robustness_matrix.py"],
    cwd=root,
    text=True,
    capture_output=True,
    check=False,
)
if proc.returncode != 0:
    print("THALARCH ROBUSTNESS-MATRIX TESTS FAILED")
    print(proc.stdout)
    print(proc.stderr)
    raise SystemExit(proc.returncode)

print("THALARCH ROBUSTNESS-MATRIX VALIDATION PASSED")
print("ablation_arms: native_skills_gates_full")
print("frozen_holdout: external_sha256_locked")
print("longbench: post_agent_hidden_tests")
print("scope_grading: forbidden_and_protected_paths")
print("cross_host: shared_tasks_shared_grader")
print("published_artifacts: sanitized_hash_attested")
print("unit_tests: passed")
