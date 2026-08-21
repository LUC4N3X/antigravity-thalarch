#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []
required = [
    root / "scripts" / "security" / "behavior_lock.py",
    root / "scripts" / "security" / "scan_agent_asset.py",
    root / "scripts" / "security" / "test_supply_chain.py",
    root / "thalarch-mode" / "hooks" / "supply_chain_guard.py",
    root / "thalarch-mode" / "skills" / "thalarch-supply-chain" / "SKILL.md",
]
for path in required:
    if not path.is_file():
        errors.append(f"missing supply-chain asset: {path.relative_to(root)}")
        continue
    if path.suffix == ".py":
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"syntax error in {path.relative_to(root)}: {exc}")

hooks_path = root / "thalarch-mode" / "hooks.json"
try:
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
except Exception as exc:
    hooks = {}
    errors.append(f"invalid hooks.json: {exc}")
serialized = json.dumps(hooks, sort_keys=True)
if "supply_chain_guard.py" not in serialized:
    errors.append("hooks.json does not wire supply_chain_guard.py")

skill_path = root / "thalarch-mode" / "skills" / "thalarch-supply-chain" / "SKILL.md"
skill_text = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
for term in ["USER_EXPLICIT", "REMOTE_UNTRUSTED", "MCP_DESCRIPTION", "SKILL_EXTERNAL", "behavior_lock.py"]:
    if term not in skill_text:
        errors.append(f"thalarch-supply-chain skill missing provenance concept: {term}")

if errors:
    print("THALARCH SUPPLY-CHAIN VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

proc = subprocess.run(
    [sys.executable, "-m", "unittest", "test_supply_chain.py"],
    cwd=root / "scripts" / "security",
    text=True,
    capture_output=True,
    check=False,
)
if proc.returncode != 0:
    print("THALARCH SUPPLY-CHAIN TESTS FAILED")
    print(proc.stdout)
    print(proc.stderr)
    raise SystemExit(proc.returncode)

print("THALARCH SUPPLY-CHAIN VALIDATION PASSED")
print("behavior_lock: sha256_file_manifest")
print("external_asset_scan: triage_not_auto_block")
print("provenance_classes: explicit")
print("runtime_lock_signal: enabled")
print("unit_tests: passed")
