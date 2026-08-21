#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
hooks = root / "thalarch-mode" / "hooks"
config_path = root / "thalarch-mode" / "hooks.json"
errors: list[str] = []

required = [
    hooks / "runtime_profile.py",
    hooks / "task_capsule.py",
    hooks / "telemetry.py",
    hooks / "convergent_stop_gate.py",
    hooks / "test_runtime_resilience.py",
]
for path in required:
    if not path.is_file():
        errors.append(f"missing runtime-resilience file: {path.relative_to(root)}")
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        errors.append(f"syntax error in {path.relative_to(root)}: {exc}")

try:
    config = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    config = {}
    errors.append(f"invalid hooks.json: {exc}")

serialized = json.dumps(config, sort_keys=True)
for term in ["convergent_stop_gate.py", "structured_verdict_gate.py", "proof_freshness_gate.py"]:
    if term not in serialized:
        errors.append(f"Stop chain missing {term}")

if (hooks / "convergent_stop_gate.py").is_file():
    text = (hooks / "convergent_stop_gate.py").read_text(encoding="utf-8")
    for term in [
        "THALARCH CONVERGENCE GUARD",
        "UNKNOWN",
        "UNVERIFIED",
        "nonterminal_count",
        "structured_verdict_object",
        "stop-convergence",
        "refresh_capsule",
        "trace_event",
    ]:
        if term not in text:
            errors.append(f"convergent_stop_gate.py missing invariant: {term}")

if (hooks / "runtime_profile.py").is_file():
    text = (hooks / "runtime_profile.py").read_text(encoding="utf-8")
    for term in ["D0", "D1", "D2", "D3", "D4", "lean", "standard", "strict", "critical"]:
        if term not in text:
            errors.append(f"runtime_profile.py missing profile concept: {term}")

if (hooks / "task_capsule.py").is_file():
    text = (hooks / "task_capsule.py").read_text(encoding="utf-8")
    for term in ["request_key", "recent_evidence", "unverified", "task-capsule"]:
        if term not in text:
            errors.append(f"task_capsule.py missing continuity concept: {term}")

if (hooks / "telemetry.py").is_file():
    text = (hooks / "telemetry.py").read_text(encoding="utf-8").lower()
    for term in ["thalarch_trace", "json", "otel", "opentelemetry", "redacted"]:
        if term not in text:
            errors.append(f"telemetry.py missing trace concept: {term}")

if errors:
    print("THALARCH RUNTIME-RESILIENCE VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

proc = subprocess.run(
    [sys.executable, "-m", "unittest", "test_runtime_resilience.py"],
    cwd=hooks,
    text=True,
    capture_output=True,
    check=False,
)
if proc.returncode != 0:
    print("THALARCH RUNTIME-RESILIENCE TESTS FAILED")
    print(proc.stdout)
    print(proc.stderr)
    raise SystemExit(proc.returncode)

print("THALARCH RUNTIME-RESILIENCE VALIDATION PASSED")
print("stop_convergence: bounded_honest_unverified_retry")
print("adaptive_profiles: D0_D4")
print("task_capsule: request_scoped")
print("telemetry: local_json_optional_otel")
print("unit_tests: passed")
