#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest

import structured_output as structured


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
        return {
            "case_id": {"type": "string"},
            "conclusion": {"type": "string", "enum": sorted(structured.CONCLUSIONS)},
            "answer": {"type": "string"},
            "claims": {"type": "array"},
            "evidence_files": {"type": "array"},
            "unverified": {"type": "array"},
        }

    def test_schema_properties_are_not_a_response(self) -> None:
        candidate = self.schema_echo()
        self.assertTrue(structured.validate_structured_response(candidate))
        self.assertIsNone(structured.extract_result([{"json_schema": candidate}], ""))

    def test_valid_direct_object_is_extracted(self) -> None:
        answer = self.valid()
        events = [{"type": "result", "result": answer}]
        self.assertEqual(structured.extract_result(events, ""), answer)

    def test_valid_json_string_is_extracted(self) -> None:
        answer = self.valid("QH-03")
        events = [{"type": "result", "result": json.dumps(answer)}]
        self.assertEqual(structured.extract_result(events, ""), answer)

    def test_echoed_schema_before_valid_answer_is_ignored(self) -> None:
        answer = self.valid()
        events = [
            {"request": {"json_schema": self.schema_echo()}},
            {"final": {"content": json.dumps(answer)}},
        ]
        self.assertEqual(structured.extract_result(events, ""), answer)

    def test_fenced_json_is_extracted(self) -> None:
        answer = self.valid("QH-06")
        text = "```json\n" + json.dumps(answer) + "\n```"
        self.assertEqual(structured.extract_result([{"content": text}], ""), answer)

    def test_json_embedded_in_text_is_extracted(self) -> None:
        answer = self.valid("QH-07")
        text = "final structured result follows: " + json.dumps(answer) + "\nend"
        self.assertEqual(structured.extract_result([{"text": text}], ""), answer)

    def test_double_encoded_json_is_extracted(self) -> None:
        answer = self.valid("QH-08")
        encoded = json.dumps(json.dumps(answer))
        self.assertEqual(structured.extract_result([{"output": encoded}], ""), answer)

    def test_raw_stdout_fallback_is_extracted(self) -> None:
        answer = self.valid("QH-02")
        stdout = "wrapper noise\n" + json.dumps(answer) + "\n"
        self.assertEqual(structured.extract_result([], stdout), answer)

    def test_wrong_enum_is_rejected(self) -> None:
        answer = self.valid()
        answer["conclusion"] = "MAYBE"
        self.assertIsNone(structured.extract_result([{"result": answer}], ""))

    def test_claim_shape_is_enforced(self) -> None:
        answer = self.valid()
        answer["claims"] = [{"claim": "x", "status": "PROVEN"}]
        self.assertIsNone(structured.extract_result([{"result": answer}], ""))

    def test_extra_top_level_fields_are_rejected(self) -> None:
        answer = self.valid()
        answer["schema"] = {"type": "object"}
        self.assertIsNone(structured.extract_result([{"result": answer}], ""))

    def test_case_id_shape_is_enforced(self) -> None:
        answer = self.valid("schema")
        self.assertIsNone(structured.extract_result([{"result": answer}], ""))


if __name__ == "__main__":
    unittest.main()
