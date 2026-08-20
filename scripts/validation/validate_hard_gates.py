#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
plugin = root / "thalarch-mode"
hooks_dir = plugin / "hooks"
hooks_json = plugin / "hooks.json"
errors: list[str] = []

required_scripts = [
    hooks_dir / "hook_utils.py",
    hooks_dir / "pre_invocation_epistemic_guard.py",
    hooks_dir / "read_target_gate.py",
    hooks_dir / "command_grounding_gate.py",
    hooks_dir / "evidence_event_recorder.py",
    hooks_dir / "evidence_event_result.py",
    hooks_dir / "stop_evidence_gate.py",
    hooks_dir / "test_hard_gates.py",
    hooks_dir / "test_finish_payload_gate.py",
    hooks_dir / "test_visual_state_gate.py",
]

for path in required_scripts:
    if not path.is_file():
        errors.append(f"missing hard-gate file: {path.relative_to(root)}")
        continue
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        errors.append(f"syntax error in {path.relative_to(root)}: {exc}")


def semantic_python_text(path: Path) -> str:
    """Return searchable Python policy text including AST string constants."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return source

    strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    return source + "\n" + "\n".join(strings)


config = {}
if not hooks_json.is_file():
    errors.append("missing thalarch-mode/hooks.json")
else:
    try:
        config = json.loads(hooks_json.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid hooks.json: {exc}")

hard = config.get("thalarch-epistemic-hard-gates") if isinstance(config, dict) else None
if not isinstance(hard, dict):
    errors.append("missing thalarch-epistemic-hard-gates hook group")
else:
    if hard.get("enabled") is not True:
        errors.append("thalarch-epistemic-hard-gates must be enabled by default")
    if not isinstance(hard.get("PreInvocation"), list) or not hard.get("PreInvocation"):
        errors.append("hard gates must define PreInvocation")
    if not isinstance(hard.get("PreToolUse"), list) or not hard.get("PreToolUse"):
        errors.append("hard gates must define PreToolUse")
    if not isinstance(hard.get("PostToolUse"), list) or not hard.get("PostToolUse"):
        errors.append("hard gates must define PostToolUse")
    if not isinstance(hard.get("Stop"), list) or not hard.get("Stop"):
        errors.append("hard gates must define Stop")

    serialized = json.dumps(hard, sort_keys=True)
    for filename in [
        "pre_invocation_epistemic_guard.py",
        "read_target_gate.py",
        "command_grounding_gate.py",
        "evidence_event_recorder.py",
        "evidence_event_result.py",
        "stop_evidence_gate.py",
    ]:
        if filename not in serialized:
            errors.append(f"hooks.json does not wire {filename}")

    pretool = hard.get("PreToolUse") if isinstance(hard.get("PreToolUse"), list) else []
    posttool = hard.get("PostToolUse") if isinstance(hard.get("PostToolUse"), list) else []
    pre_matchers = {str(item.get("matcher") or "") for item in pretool if isinstance(item, dict)}
    post_matchers = {str(item.get("matcher") or "") for item in posttool if isinstance(item, dict)}

    if not any("view_file" in matcher for matcher in pre_matchers):
        errors.append("read-target hard gate must match view_file/read_file")
    if not any("run_command" in matcher for matcher in pre_matchers):
        errors.append("command-grounding hard gate must match run_command")
    if not any("invoke_subagent" in matcher for matcher in pre_matchers):
        errors.append("evidence event recorder must match invoke_subagent")
    if not any("invoke_subagent" in matcher for matcher in post_matchers):
        errors.append("evidence event result hook must match invoke_subagent")

stop_gate = hooks_dir / "stop_evidence_gate.py"
if stop_gate.is_file():
    stop_text = semantic_python_text(stop_gate)
    for term in [
        "external_state_final_gate",
        "visual_state_final_gate",
        "final_conclusion",
        "final_unverified_items",
        "looks_like_current_external_state",
        "looks_like_visual_state",
        "has_authoritative_external_evidence",
        "has_rendered_visual_evidence",
        "latest_user_request",
        "observed_calls",
        "finish_payload_text",
        "NON_EVIDENCE_TERMINAL_TOOLS",
        "USER_EXPLICIT",
        "USER_INPUT",
        "STRONG_EXTERNAL_VERDICTS",
        "STRONG_VISUAL_VERDICTS",
        "EXTERNAL-STATE FINAL VERDICT GATE",
        "VISUAL-STATE FINAL VERDICT GATE",
    ]:
        if term not in stop_text:
            errors.append(f"stop_evidence_gate.py missing hard-gate guard: {term}")

    stop_lower = stop_text.lower()
    for concept in [
        "unknown/unverified",
        "precedence",
        "authoritative current platform/service evidence",
        "local absence",
        "corrected_premise",
        "not_found",
        "user request",
        "user's external-state request",
        "finish tool arguments",
        "final-answer content alone",
        "rendered visual state",
        "source code",
        "screenshot",
        "mobile",
        "desktop",
        "unverified ledger",
    ]:
        if concept not in stop_lower:
            errors.append(f"stop_evidence_gate.py missing verdict concept: {concept}")

tests = hooks_dir / "test_hard_gates.py"
if tests.is_file():
    tests_text = tests.read_text(encoding="utf-8")
    for term in [
        "test_stop_gate_blocks_read_only_external_corrected_premise_without_authoritative_evidence",
        "test_stop_gate_allows_read_only_external_unverified_without_authoritative_evidence",
        "test_stop_gate_allows_external_strong_verdict_after_authoritative_platform_call",
        "USER_EXPLICIT",
        "USER_INPUT",
        "The requested state cannot be established from this local checkout.",
        "Tell me the current pull request URL for this local work.",
    ]:
        if term not in tests_text:
            errors.append(f"hard-gate regression suite missing external-state case/context: {term}")

finish_tests = hooks_dir / "test_finish_payload_gate.py"
if finish_tests.is_file():
    finish_text = finish_tests.read_text(encoding="utf-8")
    for term in [
        "test_blocks_strong_external_verdict_from_finish_when_final_model_content_is_absent",
        "test_finish_answer_url_is_not_authoritative_external_evidence",
        '"name": "finish"',
        '"conclusion": conclusion',
    ]:
        if term not in finish_text:
            errors.append(f"finish-payload regression suite missing case: {term}")

visual_tests = hooks_dir / "test_visual_state_gate.py"
if visual_tests.is_file():
    visual_text = visual_tests.read_text(encoding="utf-8")
    for term in [
        "test_blocks_corrected_premise_without_rendered_visual_evidence",
        "test_requires_explicit_visual_unverified_ledger",
        "test_allows_unverified_with_concrete_missing_visual_proof",
        "test_allows_strong_visual_verdict_after_real_visual_tool_evidence",
        "looks perfect on both mobile and desktop",
        "browser_screenshot",
    ]:
        if term not in visual_text:
            errors.append(f"visual-state regression suite missing case: {term}")

if errors:
    print("THALARCH HARD-GATE VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

proc = subprocess.run(
    [
        sys.executable,
        "-m",
        "unittest",
        "test_hard_gates.py",
        "test_finish_payload_gate.py",
        "test_visual_state_gate.py",
    ],
    cwd=hooks_dir,
    text=True,
    capture_output=True,
    check=False,
)
if proc.returncode != 0:
    print("THALARCH HARD-GATE TESTS FAILED")
    print(proc.stdout)
    print(proc.stderr)
    raise SystemExit(proc.returncode)

print("THALARCH HARD-GATE VALIDATION PASSED")
print("pre_invocation_epistemic_contract: enforced")
print("exact_read_target_gate: enforced")
print("project_command_grounding: enforced")
print("event_ledger_pre_post_tool_use: enforced")
print("read_only_external_state_final_gate: enforced")
print("external_state_user_context: enforced")
print("finish_payload_final_gate: enforced")
print("visual_state_final_gate: enforced")
print("visual_unverified_ledger: enforced_when_structured")
print("python_policy_strings: ast_semantic")
print("orchestrated_stop_evidence_gate: enforced")
print("unit_tests: passed")
