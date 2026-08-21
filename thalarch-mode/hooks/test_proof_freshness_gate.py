#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_gate(payload: dict) -> dict:
    proc = subprocess.run(
        [PYTHON, str(HOOKS / "proof_freshness_gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"proof_freshness_gate.py failed: {proc.stderr}\nstdout={proc.stdout}")
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        raise AssertionError(f"proof_freshness_gate.py did not emit JSON: {proc.stdout!r} ({exc})") from exc


def request_key(request: str) -> str:
    return hashlib.sha256(request.encode("utf-8")).hexdigest()[:16]


def write_transcript(
    path: Path,
    request: str,
    conclusion: str,
    answer: str,
    *,
    unverified: list[str] | None = None,
    current_calls: list[tuple[int, str, dict]] | None = None,
    prefix_rows: list[dict] | None = None,
    user_step: int = 10,
) -> None:
    rows = list(prefix_rows or [])
    rows.append({
        "step_index": user_step,
        "source": "USER_EXPLICIT",
        "type": "USER_INPUT",
        "status": "DONE",
        "content": f"<USER_REQUEST>\n{request}\n</USER_REQUEST>",
    })
    for index, name, args in current_calls or []:
        rows.append({
            "step_index": index,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "tool_calls": [{"name": name, "args": args}],
        })
    response = {
        "case_id": "QH-99",
        "conclusion": conclusion,
        "answer": answer,
        "claims": [],
        "evidence_files": [],
        "unverified": list(unverified or []),
    }
    rows.append({
        "step_index": max([step for step, _, _ in current_calls or []], default=user_step) + 1,
        "source": "MODEL",
        "type": "PLANNER_RESPONSE",
        "status": "DONE",
        "tool_calls": [{"name": "finish", "args": response}],
    })
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def write_events(artifacts: Path, events: list[dict]) -> None:
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / ".thalarch-evidence-events.json").write_text(
        json.dumps({"events": events}),
        encoding="utf-8",
    )


def payload(root: Path, transcript: Path, artifacts: Path) -> dict:
    return {
        "fullyIdle": True,
        "terminationReason": "TERMINAL_STEP_TYPE",
        "transcriptPath": str(transcript),
        "artifactDirectoryPath": str(artifacts),
        "workspacePaths": [str(root)],
    }


class ProofFreshnessGateTests(unittest.TestCase):
    def test_blocks_proven_test_status_without_successful_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            request = "Tell me whether all tests pass right now."
            write_transcript(transcript, request, "PROVEN", "All tests pass right now.")
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])
            self.assertIn("FRESH PROOF GATE", result["reason"])
            self.assertIn("successful matching execution", result["reason"])

    def test_failed_current_test_command_is_not_runtime_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            request = "Tell me whether all tests pass right now."
            write_transcript(
                transcript,
                request,
                "PROVEN",
                "All tests pass right now.",
                current_calls=[(11, "run_command", {"CommandLine": "python -m unittest discover -s tests"})],
            )
            write_events(artifacts, [{
                "step": 11,
                "name": "run_command",
                "argsText": json.dumps({"CommandLine": "python -m unittest discover -s tests"}).lower(),
                "requestKey": request_key(request),
                "status": "failed",
                "error": "nonzero exit code 1",
            }])
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])

    def test_successful_current_test_command_can_prove_runtime_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            request = "Tell me whether all tests pass right now."
            write_transcript(
                transcript,
                request,
                "PROVEN",
                "All tests pass right now.",
                current_calls=[(11, "run_command", {"CommandLine": "python -m unittest discover -s tests"})],
            )
            write_events(artifacts, [{
                "step": 11,
                "name": "run_command",
                "argsText": json.dumps({"CommandLine": "python -m unittest discover -s tests"}).lower(),
                "requestKey": request_key(request),
                "status": "completed",
            }])
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("stop", result["decision"])

    def test_stale_runtime_event_from_previous_request_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            old_request = "Run the tests once."
            request = "Do all tests pass right now?"
            write_transcript(transcript, request, "PROVEN", "All tests pass right now.")
            write_events(artifacts, [{
                "step": 2,
                "name": "run_command",
                "argsText": json.dumps({"CommandLine": "python -m unittest discover -s tests"}).lower(),
                "requestKey": request_key(old_request),
                "status": "completed",
            }])
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])

    def test_stale_external_platform_call_cannot_prove_new_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            prefix = [
                {
                    "step_index": 0,
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "status": "DONE",
                    "content": "<USER_REQUEST>Check GitHub.</USER_REQUEST>",
                },
                {
                    "step_index": 1,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "status": "DONE",
                    "tool_calls": [{"name": "github_search_prs", "args": {"repository": "owner/repo"}}],
                },
            ]
            request = "Tell me the current pull request URL now."
            write_transcript(
                transcript,
                request,
                "PROVEN",
                "The current pull request state is proven.",
                prefix_rows=prefix,
            )
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])
            self.assertIn("latest user request", result["reason"])

    def test_stale_screenshot_cannot_prove_new_visual_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            prefix = [
                {
                    "step_index": 0,
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "status": "DONE",
                    "content": "<USER_REQUEST>Take a screenshot.</USER_REQUEST>",
                },
                {
                    "step_index": 1,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "status": "DONE",
                    "tool_calls": [{"name": "browser_screenshot", "args": {"viewport": "desktop"}}],
                },
            ]
            request = "Confirm the page looks perfect on mobile and desktop now."
            write_transcript(
                transcript,
                request,
                "PROVEN",
                "The page looks perfect on mobile and desktop.",
                prefix_rows=prefix,
            )
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])

    def test_runtime_unverified_ledger_must_name_missing_runtime_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            request = "Tell me whether all tests pass right now."
            write_transcript(
                transcript,
                request,
                "UNVERIFIED",
                "Current test status is unverified.",
                unverified=["More evidence is needed."],
            )
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("continue", result["decision"])
            self.assertIn("unverified ledger", result["reason"])

    def test_runtime_unverified_with_concrete_missing_run_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            request = "Tell me whether all tests pass right now."
            write_transcript(
                transcript,
                request,
                "UNVERIFIED",
                "Current test status is unverified.",
                unverified=["The full test suite was not executed in this request."],
            )
            result = run_gate(payload(root, transcript, artifacts))
            self.assertEqual("stop", result["decision"])


if __name__ == "__main__":
    unittest.main()
