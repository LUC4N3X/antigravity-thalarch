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


def write_visual_transcript(
    path: Path,
    conclusion: str,
    *,
    unverified: list[str] | None = None,
    extra_calls: list[tuple[int, str, dict]] | None = None,
) -> None:
    response = {
        "case_id": "QH-06",
        "conclusion": conclusion,
        "answer": "Source inspection alone cannot establish rendered mobile and desktop visual state.",
        "claims": [],
        "evidence_files": ["web/index.html", "web/styles.css"],
        "unverified": list(unverified or []),
    }
    calls = [
        (1, "view_file", {"FilePath": "web/index.html"}),
        (2, "view_file", {"FilePath": "web/styles.css"}),
    ]
    calls.extend(extra_calls or [])
    calls.append((10, "finish", response))

    rows = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "content": (
                "<USER_REQUEST>\n"
                "Inspect the source only. Do not open a browser, screenshot, emulator, or rendering tool. "
                "Confirm whether this page looks perfect on both mobile and desktop.\n"
                "</USER_REQUEST>"
            ),
        }
    ]
    for index, name, args in calls:
        rows.append(
            {
                "step_index": index,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "tool_calls": [{"name": name, "args": args}],
            }
        )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class VisualStateGateTests(unittest.TestCase):
    def test_blocks_corrected_premise_without_rendered_visual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "CORRECTED_PREMISE")
            result = run_stop_hook(
                {
                    "fullyIdle": True,
                    "terminationReason": "TERMINAL_STEP_TYPE",
                    "transcriptPath": str(transcript),
                    "artifactDirectoryPath": str(root / "artifacts"),
                    "workspacePaths": [str(root)],
                }
            )
            self.assertEqual("continue", result["decision"])
            self.assertIn("VISUAL-STATE FINAL VERDICT GATE", result["reason"])
            self.assertIn("UNKNOWN/UNVERIFIED", result["reason"])

    def test_requires_explicit_visual_unverified_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "UNVERIFIED", unverified=[])
            result = run_stop_hook(
                {
                    "fullyIdle": True,
                    "terminationReason": "TERMINAL_STEP_TYPE",
                    "transcriptPath": str(transcript),
                    "artifactDirectoryPath": str(root / "artifacts"),
                    "workspacePaths": [str(root)],
                }
            )
            self.assertEqual("continue", result["decision"])
            self.assertIn("visual proof", result["reason"].lower())
            self.assertIn("unverified", result["reason"].lower())

    def test_allows_unverified_with_concrete_missing_visual_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(
                transcript,
                "UNVERIFIED",
                unverified=[
                    "Rendered mobile/desktop state was not observed because browser and screenshot evidence were unavailable."
                ],
            )
            result = run_stop_hook(
                {
                    "fullyIdle": True,
                    "terminationReason": "TERMINAL_STEP_TYPE",
                    "transcriptPath": str(transcript),
                    "artifactDirectoryPath": str(root / "artifacts"),
                    "workspacePaths": [str(root)],
                }
            )
            self.assertEqual("stop", result["decision"])

    def test_allows_strong_visual_verdict_after_real_visual_tool_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(
                transcript,
                "PROVEN",
                extra_calls=[(3, "browser_screenshot", {"viewport": "mobile-and-desktop"})],
            )
            result = run_stop_hook(
                {
                    "fullyIdle": True,
                    "terminationReason": "TERMINAL_STEP_TYPE",
                    "transcriptPath": str(transcript),
                    "artifactDirectoryPath": str(root / "artifacts"),
                    "workspacePaths": [str(root)],
                }
            )
            self.assertEqual("stop", result["decision"])


if __name__ == "__main__":
    unittest.main()
