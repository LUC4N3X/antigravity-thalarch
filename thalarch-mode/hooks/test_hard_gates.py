#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_hook(script: str, payload: dict) -> dict:
    proc = subprocess.run(
        [PYTHON, str(HOOKS / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"{script} failed: {proc.stderr}\nstdout={proc.stdout}")
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        raise AssertionError(f"{script} did not emit JSON: {proc.stdout!r} ({exc})") from exc


def write_transcript(path: Path, calls: list[tuple[int, str, dict]], final: str = "") -> None:
    rows = []
    for index, name, args in calls:
        rows.append({
            "step_index": index,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "tool_calls": [{"name": name, "args": args}],
        })
    if final:
        rows.append({
            "step_index": max([i for i, _, _ in calls], default=0) + 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "content": final,
        })
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class HardGateTests(unittest.TestCase):
    def test_pre_invocation_injects_evidence_contract(self) -> None:
        result = run_hook("pre_invocation_epistemic_guard.py", {"invocationNum": 0})
        self.assertIn("injectSteps", result)
        self.assertIn("UNVERIFIED", result["injectSteps"][0]["ephemeralMessage"])

    def test_read_target_gate_denies_missing_exact_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = {
                "workspacePaths": [str(root)],
                "toolCall": {"name": "view_file", "args": {"FilePath": "invented/Foo.kt"}},
            }
            result = run_hook("read_target_gate.py", payload)
            self.assertEqual("deny", result["decision"])

    def test_read_target_gate_allows_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Foo.kt").write_text("class Foo", encoding="utf-8")
            payload = {
                "workspacePaths": [str(root)],
                "toolCall": {"name": "view_file", "args": {"FilePath": "Foo.kt"}},
            }
            result = run_hook("read_target_gate.py", payload)
            self.assertEqual("allow", result["decision"])

    def test_command_gate_denies_invented_npm_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
            payload = {
                "workspacePaths": [str(root)],
                "toolCall": {"name": "run_command", "args": {"CommandLine": "npm run hallucinated", "Cwd": str(root)}},
            }
            result = run_hook("command_grounding_gate.py", payload)
            self.assertEqual("deny", result["decision"])

    def test_command_gate_allows_declared_npm_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
            payload = {
                "workspacePaths": [str(root)],
                "toolCall": {"name": "run_command", "args": {"CommandLine": "npm run test", "Cwd": str(root)}},
            }
            result = run_hook("command_grounding_gate.py", payload)
            self.assertEqual("allow", result["decision"])

    def test_command_gate_denies_missing_local_python_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = {
                "workspacePaths": [str(root)],
                "toolCall": {"name": "run_command", "args": {"CommandLine": "python scripts/nope.py", "Cwd": str(root)}},
            }
            result = run_hook("command_grounding_gate.py", payload)
            self.assertEqual("deny", result["decision"])

    def test_stop_gate_blocks_orchestrated_mutation_without_independent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_transcript(transcript, [
                (1, "invoke_subagent", {"agent": "thalarch-kotlin-engineer", "prompt": "implement"}),
            ])
            result = run_hook("stop_evidence_gate.py", {
                "fullyIdle": True,
                "terminationReason": "NO_TOOL_CALL",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("continue", result["decision"])
            self.assertIn("fact-check", result["reason"])

    def test_stop_gate_allows_fact_check_then_cold_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_transcript(transcript, [
                (1, "invoke_subagent", {"agent": "thalarch-java-engineer"}),
                (2, "invoke_subagent", {"agent": "thalarch-fact-checker"}),
                (3, "invoke_subagent", {"agent": "thalarch-verifier"}),
            ])
            result = run_hook("stop_evidence_gate.py", {
                "fullyIdle": True,
                "terminationReason": "model_stop",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("stop", result["decision"])

    def test_visual_work_requires_visual_review_before_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_transcript(transcript, [
                (1, "invoke_subagent", {"agent": "thalarch-visual-director"}),
                (2, "invoke_subagent", {"agent": "thalarch-fact-checker"}),
                (3, "invoke_subagent", {"agent": "thalarch-verifier"}),
            ])
            result = run_hook("stop_evidence_gate.py", {
                "fullyIdle": True,
                "terminationReason": "NO_TOOL_CALL",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("continue", result["decision"])
            self.assertIn("vision review", result["reason"])

    def test_honest_unverified_escape_prevents_infinite_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_transcript(
                transcript,
                [(1, "invoke_subagent", {"agent": "thalarch-python-engineer"})],
                final="The verifier is unavailable in this environment, so runtime completion remains UNVERIFIED.",
            )
            result = run_hook("stop_evidence_gate.py", {
                "fullyIdle": True,
                "terminationReason": "NO_TOOL_CALL",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("stop", result["decision"])

    def test_specialist_direct_edit_does_not_deadlock_on_parent_only_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_transcript(transcript, [
                (1, "replace_file_content", {"FilePath": "Foo.kt"}),
                (2, "run_command", {"CommandLine": "./gradlew test"}),
            ])
            result = run_hook("stop_evidence_gate.py", {
                "fullyIdle": True,
                "terminationReason": "model_stop",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("stop", result["decision"])


if __name__ == "__main__":
    unittest.main()
