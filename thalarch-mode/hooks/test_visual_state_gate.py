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
        [PYTHON, str(HOOKS / "structured_verdict_gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOKS,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"structured_verdict_gate.py failed: {proc.stderr}\nstdout={proc.stdout}")
    return json.loads(proc.stdout)


def wrap_finish(response: dict, transport: str) -> dict:
    if transport == "direct":
        return response
    if transport == "result":
        return {"result": response}
    if transport == "fenced":
        return {"output": "```json\n" + json.dumps(response) + "\n```"}
    if transport == "double":
        return {"response": json.dumps(json.dumps(response))}
    raise ValueError(f"unknown transport: {transport}")


def write_visual_transcript(
    path: Path,
    conclusion: str,
    *,
    unverified: list[str] | None = None,
    extra_calls: list[tuple[int, str, dict]] | None = None,
    planner_content: str | None = None,
    transport: str = "direct",
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

    if planner_content is not None:
        rows.append(
            {
                "step_index": 9,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "content": planner_content,
            }
        )

    rows.append(
        {
            "step_index": 10,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "tool_calls": [{"name": "finish", "args": wrap_finish(response, transport)}],
        }
    )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def payload_for(root: Path, transcript: Path) -> dict:
    return {
        "fullyIdle": True,
        "terminationReason": "TERMINAL_STEP_TYPE",
        "transcriptPath": str(transcript),
        "artifactDirectoryPath": str(root / "artifacts"),
        "workspacePaths": [str(root)],
    }


class VisualStateGateTests(unittest.TestCase):
    def test_blocks_corrected_premise_without_rendered_visual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "CORRECTED_PREMISE")
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("visual", result["reason"].lower())
            self.assertIn("unknown/unverified", result["reason"].lower())

    def test_requires_explicit_visual_unverified_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "UNVERIFIED", unverified=[])
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("visual", result["reason"].lower())
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
            result = run_stop_hook(payload_for(root, transcript))
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
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("stop", result["decision"])

    def test_structured_finish_precedes_planner_prose_for_visual_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(
                transcript,
                "UNVERIFIED",
                unverified=[],
                planner_content="I cannot certify the appearance from source inspection alone.",
            )
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("structured verdict gate", result["reason"].lower())
            self.assertIn("unverified ledger", result["reason"].lower())

    def test_wrapped_visual_ledger_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "UNVERIFIED", unverified=[], transport="result")
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("structured verdict gate", result["reason"].lower())

    def test_fenced_visual_ledger_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "UNVERIFIED", unverified=[], transport="fenced")
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("structured verdict gate", result["reason"].lower())

    def test_double_encoded_visual_ledger_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(transcript, "UNVERIFIED", unverified=[], transport="double")
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("continue", result["decision"])
            self.assertIn("structured verdict gate", result["reason"].lower())

    def test_wrapped_visual_reason_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transcript = root / "transcript.jsonl"
            write_visual_transcript(
                transcript,
                "UNVERIFIED",
                unverified=["Browser screenshot evidence for mobile and desktop was not captured."],
                transport="result",
            )
            result = run_stop_hook(payload_for(root, transcript))
            self.assertEqual("stop", result["decision"])


if __name__ == "__main__":
    unittest.main()
