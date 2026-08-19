#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
bench = root / "benchmarks"
quick = bench / "quick"
errors: list[str] = []

required = [
    bench / "README.md",
    bench / "cases.json",
    bench / "rubric.json",
    bench / "result-template.json",
    bench / "score_run.py",
    quick / "README.md",
    quick / "cases.json",
    quick / "response.schema.json",
    quick / "run_antigravity.py",
]
for path in required:
    if not path.is_file():
        errors.append(f"missing benchmark file: {path.relative_to(root)}")

for path in [
    bench / "cases.json",
    bench / "rubric.json",
    bench / "result-template.json",
    quick / "cases.json",
    quick / "response.schema.json",
]:
    if not path.is_file():
        continue
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid JSON in {path.relative_to(root)}: {exc}")

for script in [bench / "score_run.py", quick / "run_antigravity.py"]:
    if not script.is_file():
        continue
    try:
        compile(script.read_text(encoding="utf-8"), str(script), "exec")
    except SyntaxError as exc:
        errors.append(f"syntax error in {script.relative_to(root)}: {exc}")

if not errors:
    cases = json.loads((bench / "cases.json").read_text(encoding="utf-8"))
    entries = cases.get("cases") if isinstance(cases, dict) else None
    if not isinstance(entries, list) or len(entries) < 20:
        errors.append("benchmark suite must contain at least 20 diverse cases")
    else:
        ids = [str(case.get("id") or "") for case in entries if isinstance(case, dict)]
        if len(ids) != len(set(ids)):
            errors.append("benchmark case ids must be unique")
        for case in entries:
            if not isinstance(case, dict):
                errors.append("every benchmark case must be an object")
                continue
            for key in ["id", "category", "title", "prompt", "fixture_requirement", "success_signal"]:
                if not isinstance(case.get(key), str) or not case[key].strip():
                    errors.append(f"benchmark case {case.get('id', '?')} missing {key}")

    rubric = json.loads((bench / "rubric.json").read_text(encoding="utf-8"))
    if rubric.get("version") != "1.0.0":
        errors.append("benchmark rubric version must remain 1.0.0")
    required_types = {
        "REPO_FACT", "API_VERSION", "COMMAND", "RUNTIME_RESULT", "EXTERNAL_STATE",
        "VISUAL_STATE", "PROOF_SUBSTITUTION", "CITATION_SOURCE", "OTHER",
    }
    weights = rubric.get("hallucination_weights", {})
    if not required_types.issubset(set(weights)):
        errors.append("benchmark rubric missing hallucination taxonomy weights")

if not errors:
    quick_cases = json.loads((quick / "cases.json").read_text(encoding="utf-8"))
    if quick_cases.get("version") != "1.0.0":
        errors.append("quick benchmark version must remain 1.0.0")
    entries = quick_cases.get("cases")
    if not isinstance(entries, list) or len(entries) != 8:
        errors.append("quick benchmark must contain exactly 8 deterministic cases")
    else:
        ids = [str(case.get("id") or "") for case in entries if isinstance(case, dict)]
        if len(ids) != len(set(ids)):
            errors.append("quick benchmark case ids must be unique")
        expected_ids = {f"QH-{n:02d}" for n in range(1, 9)}
        if set(ids) != expected_ids:
            errors.append("quick benchmark ids must be QH-01 through QH-08")
        for case in entries:
            if not isinstance(case, dict):
                errors.append("every quick benchmark case must be an object")
                continue
            for key in [
                "id", "title", "category", "hallucination_type", "prompt", "success_signal",
                "allowed_conclusions", "required_text_regex", "forbidden_text_regex",
                "false_claim_regex", "files",
            ]:
                if key not in case:
                    errors.append(f"quick benchmark case {case.get('id', '?')} missing {key}")
            if not isinstance(case.get("files"), dict) or not case["files"]:
                errors.append(f"quick benchmark case {case.get('id', '?')} must define fixture files")

    schema = json.loads((quick / "response.schema.json").read_text(encoding="utf-8"))
    required_schema_fields = {"case_id", "conclusion", "answer", "claims", "evidence_files", "unverified"}
    if set(schema.get("required", [])) != required_schema_fields:
        errors.append("quick benchmark response schema required fields changed unexpectedly")

    runner = (quick / "run_antigravity.py").read_text(encoding="utf-8")
    for term in [
        "class BenchmarkInfraError",
        "def set_thalarch_plugin_state",
        "BENCHMARK INFRA_ERROR",
        "No hallucination score was recorded for this infrastructure failure.",
        "--output-format=stream-json",
        "--json-schema=",
        "proc = run_text(cmd, cwd=workspace)",
    ]:
        if term not in runner:
            errors.append(f"quick benchmark runner missing infrastructure guard: {term}")
    if "def detect_thalarch_plugin_state" in runner:
        errors.append("quick benchmark must not infer effective plugin state from plugin list")
    if "--cwd" in runner:
        errors.append("Antigravity CLI 1.1.x does not expose --cwd; benchmark must use subprocess cwd")
    if '"type": "OTHER",\n                "claim": "Antigravity print-mode run failed."' in runner:
        errors.append("CLI infrastructure failures must not be recorded as hallucinations")

# Scorer smoke test with a paired native/Thalarch result.
score = bench / "score_run.py"
if not errors and score.is_file():
    template = json.loads((bench / "result-template.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        native = dict(template)
        native.update({
            "case_id": "H-01",
            "host": "test-host",
            "thalarch": False,
            "task_status": "FAIL",
            "hallucinations": [{
                "type": "REPO_FACT",
                "claim": "invented symbol",
                "evidence": "symbol absent",
                "corrected_before_final": False,
            }],
        })
        guarded = dict(template)
        guarded.update({
            "case_id": "H-01",
            "host": "test-host",
            "thalarch": True,
            "task_status": "PASS",
            "hallucinations": [],
        })
        native_path = temp / "native.json"
        guarded_path = temp / "thalarch.json"
        native_path.write_text(json.dumps(native), encoding="utf-8")
        guarded_path.write_text(json.dumps(guarded), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(score), str(native_path), str(guarded_path)],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            errors.append(f"benchmark scorer smoke test failed: {proc.stderr or proc.stdout}")
        elif "Paired Thalarch delta" not in proc.stdout or "test-host | H-01" not in proc.stdout:
            errors.append("benchmark scorer did not produce paired comparison output")

if errors:
    print("THALARCH BENCHMARK VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH BENCHMARK VALIDATION PASSED")
print("version: 1.0.0 (fixed)")
print("cross_model_cases: >=20")
print("quick_antigravity_cases: 8")
print("quick_structured_output: enforced")
print("quick_cli_workdir: subprocess_cwd")
print("quick_infra_errors: separated_from_hallucinations")
print("hallucination_taxonomy: enforced")
print("paired_scorer: passed")
