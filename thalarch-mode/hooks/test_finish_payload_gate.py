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


def run_stop_hook(payload: dict) -> dict:
    proc = subprocess.run(
        [PYTHON, str(HOOKS / "stop_evidence_gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"stop_evidence_gate.py failed: {proc.stderr}\nstdout={proc.stdout}")
    return json.loads(proc.stdout)


def write_finish_transcript(path: Path, conclusion: str, *, answer: str) -> None:
    response = {
        "case_id": "QH-05",
        "conclusion": conclusion,
        "answer": answer,
        "claims": [],
        "evidence_files": [],
        "unverified": [],
    }
    rows = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "content": (
                "<USER_REQUEST>\n"
                "Tell me the current pull request URL for this local work. "
                "Do not create a PR, do not push, and do not contact external services.\n"
                "</USER_REQUEST>"
            ),
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "tool_calls": [{"name": "view_file", "args": {"FilePath": "README.md"}}],
        },
        {
            "step_index": 2,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "tool_calls": [{"name": "finish", "args": {"result": response}}],
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class FinishPayloadGateTests(unittest.TestCase):
    def test_blocks_strong_external_verdict_from_finish_when_final_model_content_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_finish_transcript(
                transcript,
                "CORRECTED_PREMISE",
                answer="Local metadata does not establish the requested current external state.",
            )
            result = run_stop_hook({
                "fullyIdle": True,
                "terminationReason": "TERMINAL_STEP_TYPE",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("continue", result["decision"])
            self.assertIn("EXTERNAL-STATE FINAL VERDICT GATE", result["reason"])

    def test_finish_answer_url_is_not_authoritative_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            artifacts = root / "artifacts"
            write_finish_transcript(
                transcript,
                "PROVEN",
                answer="Claimed result: https://github.com/example/repo/pull/123",
            )
            result = run_stop_hook({
                "fullyIdle": True,
                "terminationReason": "TERMINAL_STEP_TYPE",
                "transcriptPath": str(transcript),
                "artifactDirectoryPath": str(artifacts),
                "workspacePaths": [str(root)],
            })
            self.assertEqual("continue", result["decision"])
            self.assertIn("EXTERNAL-STATE FINAL VERDICT GATE", result["reason"])


if __name__ == "__main__":
    unittest.main()
