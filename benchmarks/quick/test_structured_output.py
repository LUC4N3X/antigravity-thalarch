#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest

import run_antigravity as runner


class StructuredOutputTests(unittest.TestCase):
    def valid(self, case_id: str = "QH-05") -> dict:
        return {
            "case_id": case_id,
            "conclusion": "UNVERIFIED",
            "answer": "The requested state was not observed.",
            "claims": [
                {
                    "claim": "The requested state was not observed.",
                    "status": "UNVERIFIED",
                    "evidence": "No matching evidence was available in the benchmark workspace.",
                }
            ],
            "evidence_files": [],
            "unverified": ["requested state"],
        }

    def schema_echo(self) -> dict:
        schema = runner.load_json(runner.SCHEMA_PATH)
        # This is the exact trap seen in Antigravity stream-json: schema properties
        # contain case_id/conclusion/claims keys but are not a model response.
        return schema["properties"]

    def test_schema_properties_are_not_a_response(self) -> None:
        candidate = self.schema_echo()
        self.assertTrue(runner.validate_structured_response(candidate))
        self.assertIsNone(runner.extract_result([{"json_schema": candidate}], ""))

    def test_valid_direct_object_is_extracted(self) -> None:
        answer = self.valid()
        events = [{"type": "result", "result": answer}]
        self.assertEqual(runner.extract_result(events, ""), answer)

    def test_valid_json_string_is_extracted(self) -> None:
        answer = self.valid("QH-03")
        events = [{"type": "result", "result": json.dumps(answer)}]
        self.assertEqual(runner.extract_result(events, ""), answer)

    def test_echoed_schema_before_valid_answer_is_ignored(self) -> None:
        answer = self.valid()
        events = [
            {"request": {"json_schema": self.schema_echo()}},
            {"final": {"content": json.dumps(answer)}},
        ]
        self.assertEqual(runner.extract_result(events, ""), answer)

    def test_wrong_enum_is_rejected(self) -> None:
        answer = self.valid()
        answer["conclusion"] = "MAYBE"
        self.assertIsNone(runner.extract_result([{"result": answer}], ""))

    def test_claim_shape_is_enforced(self) -> None:
        answer = self.valid()
        answer["claims"] = [{"claim": "x", "status": "PROVEN"}]
        self.assertIsNone(runner.extract_result([{"result": answer}], ""))

    def test_extra_top_level_fields_are_rejected(self) -> None:
        answer = self.valid()
        answer["schema"] = {"type": "object"}
        self.assertIsNone(runner.extract_result([{"result": answer}], ""))


if __name__ == "__main__":
    unittest.main()
