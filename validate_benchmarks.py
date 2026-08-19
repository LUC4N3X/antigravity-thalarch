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
    quick / "judge.py",
    quick / "test_judge.py",
    quick / "plugin_integrity.py",
    quick / "run_antigravity.py",
    quick / "run_pair.py",
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

for script in [
    bench / "score_run.py",
    quick / "judge.py",
    quick / "test_judge.py",
    quick / "plugin_integrity.py",
    quick / "run_antigravity.py",
    quick / "run_pair.py",
]:
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
    if quick_cases.get("protocol_revision") != 2:
        errors.append("quick benchmark protocol revision must be 2")
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
        by_id = {str(case.get("id")): case for case in entries if isinstance(case, dict)}
        for case in entries:
            if not isinstance(case, dict):
                errors.append("every quick benchmark case must be an object")
                continue
            for key in [
                "id", "title", "category", "hallucination_type", "prompt", "success_signal",
                "allowed_conclusions", "hallucination_conclusions", "required_text_regex",
                "required_evidence_regex", "requires_unverified", "required_unverified_regex",
                "forbidden_text_regex", "false_claim_regex", "files",
            ]:
                if key not in case:
                    errors.append(f"quick benchmark case {case.get('id', '?')} missing {key}")
            if not isinstance(case.get("files"), dict) or not case["files"]:
                errors.append(f"quick benchmark case {case.get('id', '?')} must define fixture files")

        qh04 = by_id.get("QH-04", {})
        if qh04.get("required_text_regex"):
            errors.append("QH-04 must grade unrun-suite honesty semantically, not require README/command prose")
        if qh04.get("requires_unverified") is not True:
            errors.append("QH-04 must require explicit unverified runtime state")
        qh06 = by_id.get("QH-06", {})
        if qh06.get("forbidden_text_regex"):
            errors.append("QH-06 must not use raw phrase bans that misclassify negated visual statements")
        if qh06.get("requires_unverified") is not True:
            errors.append("QH-06 must require explicit unverified render state")

    schema = json.loads((quick / "response.schema.json").read_text(encoding="utf-8"))
    required_schema_fields = {"case_id", "conclusion", "answer", "claims", "evidence_files", "unverified"}
    if set(schema.get("required", [])) != required_schema_fields:
        errors.append("quick benchmark response schema required fields changed unexpectedly")
    conclusion_desc = str(schema.get("properties", {}).get("conclusion", {}).get("description", "")).lower()
    if "user's main factual proposition" not in conclusion_desc:
        errors.append("quick benchmark conclusion must explicitly target the user's factual proposition")
    answer_desc = str(schema.get("properties", {}).get("answer", {}).get("description", "")).lower()
    if "claims" not in answer_desc or "material factual assertion" not in answer_desc:
        errors.append("quick benchmark answer schema must require material assertions to be represented in claims")

    runner = (quick / "run_antigravity.py").read_text(encoding="utf-8")
    for term in [
        "PROTOCOL_REVISION = 2",
        "class BenchmarkInfraError",
        "def set_thalarch_plugin_state",
        "def build_cli_env",
        "def protocol_fingerprint",
        "def ensure_run_manifest",
        "BENCHMARK INFRA_ERROR",
        "No hallucination score was recorded for this infrastructure failure.",
        "--add-dir=",
        "--output-format=stream-json",
        "--json-schema=",
        "proc = run_text(cmd, cwd=workspace, env=build_cli_env())",
        "list_dir and view_file",
        "Do not use grep_search, run_command, browser, web, MCP, or external tools.",
        "/thalarch-mode",
        "slash-skill:thalarch-mode",
        "--repeat",
        "--effort",
        "protocol_fingerprint",
        "requested_model",
        "USER'S MAIN FACTUAL PROPOSITION",
    ]:
        if term not in runner:
            errors.append(f"quick benchmark runner missing protocol guard: {term}")
    if "--agent=thalarch-orchestrator" in runner:
        errors.append("quick benchmark must test the Thalarch skill directly, not switch primary agent presets")
    if "def detect_thalarch_plugin_state" in runner:
        errors.append("quick benchmark must not infer effective plugin state from plugin list")
    if "--cwd" in runner:
        errors.append("Antigravity CLI 1.1.x does not expose --cwd; benchmark must use subprocess cwd")
    if "--dangerously-skip-permissions" in runner:
        errors.append("quick benchmark must not bypass all user permissions")

    plugin_integrity = (quick / "plugin_integrity.py").read_text(encoding="utf-8")
    for term in [
        "DEFAULT_STAGED_PLUGIN",
        "antigravity-cli",
        "behavior_files",
        "verify_plugin_tree",
        "source_fingerprint",
        "staged_fingerprint",
        "missing",
        "extra",
        "mismatched",
    ]:
        if term not in plugin_integrity:
            errors.append(f"quick plugin-integrity checker missing control: {term}")

    pair_driver = (quick / "run_pair.py").read_text(encoding="utf-8")
    for term in [
        "--model",
        "required=True",
        "default=3",
        "counterbalanced per case/trial",
        "native_first = (trial + case_index) % 2 == 1",
        "runner.set_thalarch_plugin_state",
        "runner.run_case",
        "score_run.py",
        "run_validator()",
        "verify_plugin_tree()",
        "plugin_match_verified",
        "plugin_source_fingerprint",
        "plugin_staged_fingerprint",
        "staged Antigravity CLI copy",
    ]:
        if term not in pair_driver:
            errors.append(f"quick paired driver missing control: {term}")

    judge = (quick / "judge.py").read_text(encoding="utf-8")
    for term in [
        "SUPPORTED_STATUSES",
        "hallucination_conclusions",
        "required_evidence_regex",
        "requires_unverified",
        "Hard forbidden outputs",
        "PROVEN/SUPPORTED",
    ]:
        if term not in judge:
            errors.append(f"quick benchmark judge missing semantic guard: {term}")

    scorer = (bench / "score_run.py").read_text(encoding="utf-8")
    for term in [
        "UNVERIFIED:plugin-checkout",
        "INVALID:plugin-fingerprint",
        "plugin_match_verified",
        "plugin_source_fingerprint",
        "plugin_staged_fingerprint",
    ]:
        if term not in scorer:
            errors.append(f"benchmark scorer missing plugin-integrity control: {term}")

if not errors:
    proc = subprocess.run(
        [sys.executable, str(quick / "test_judge.py")],
        cwd=quick,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(f"quick benchmark judge regression tests failed: {proc.stderr or proc.stdout}")

score = bench / "score_run.py"
if not errors and score.is_file():
    template = json.loads((bench / "result-template.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        native = dict(template)
        native.update({
            "case_id": "H-01",
            "trial": 1,
            "host": "test-host",
            "model": "test-model",
            "requested_model": "test-model",
            "effort": "high",
            "protocol_revision": 2,
            "protocol_fingerprint": "abc",
            "benchmark_revision": "def",
            "agy_version": "1.1.15",
            "thalarch": False,
            "thalarch_activation": "native-default-agent",
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
            "trial": 1,
            "host": "test-host",
            "model": "test-model",
            "requested_model": "test-model",
            "effort": "high",
            "protocol_revision": 2,
            "protocol_fingerprint": "abc",
            "benchmark_revision": "def",
            "agy_version": "1.1.15",
            "thalarch": True,
            "thalarch_activation": "slash-skill:thalarch-mode",
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
        elif "comparison_integrity: EXPLORATORY" not in proc.stdout:
            errors.append("benchmark scorer must label a one-trial comparison as EXPLORATORY")

if errors:
    print("THALARCH BENCHMARK VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH BENCHMARK VALIDATION PASSED")
print("version: 1.0.0 (fixed)")
print("cross_model_cases: >=20")
print("quick_antigravity_cases: 8")
print("quick_protocol_revision: 2")
print("quick_structured_verdict_semantics: enforced")
print("quick_judge_regressions: passed")
print("quick_cli_workdir: subprocess_cwd")
print("quick_cli_workspace: add_dir")
print("quick_read_tools: list_dir_view_file_only")
print("quick_permission_bypass: forbidden")
print("quick_infra_errors: separated_from_hallucinations")
print("quick_paired_manifest: model_effort_revision_fingerprint")
print("quick_repeated_trials: supported")
print("quick_counterbalanced_driver: enforced")
print("quick_plugin_checkout_integrity: enforced")
print("quick_thalarch_activation: explicit_skill_slash_command")
print("hallucination_taxonomy: enforced")
print("paired_scorer: passed")
