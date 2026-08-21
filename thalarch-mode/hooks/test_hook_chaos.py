from __future__ import annotations

import json
import random
import string
import unittest

import evidence_event_result
import structured_verdict_gate


class StructuredTransportChaosTests(unittest.TestCase):
    def test_seeded_transport_fuzz_never_raises(self):
        rng = random.Random(20260821)

        def atom():
            choices = [
                None,
                True,
                False,
                rng.randint(-10_000, 10_000),
                "".join(rng.choice(string.printable) for _ in range(rng.randint(0, 80))),
            ]
            return rng.choice(choices)

        def value(depth=0):
            if depth >= 4 or rng.random() < 0.45:
                return atom()
            if rng.random() < 0.5:
                return [value(depth + 1) for _ in range(rng.randint(0, 5))]
            return {
                "".join(rng.choice(string.ascii_letters) for _ in range(rng.randint(1, 10))): value(depth + 1)
                for _ in range(rng.randint(0, 5))
            }

        for _ in range(300):
            candidate = value()
            structured_verdict_gate.structured_verdict_object([candidate])
            if rng.random() < 0.5:
                encoded = json.dumps(candidate)
                structured_verdict_gate.structured_verdict_object([encoded])

    def test_deeply_wrapped_honest_verdict_is_recovered(self):
        verdict = {
            "conclusion": "UNVERIFIED",
            "unverified": ["Missing browser screenshot proof."],
        }
        wrapped = {"event": {"payload": json.dumps({"answer": "```json\n" + json.dumps(verdict) + "\n```"})}}
        found = structured_verdict_gate.structured_verdict_object([wrapped])
        self.assertIsNotNone(found)
        self.assertEqual(found["conclusion"], "UNVERIFIED")

    def test_schema_like_noise_is_not_a_verdict_without_conclusion_value(self):
        noise = {
            "type": "object",
            "properties": {
                "conclusion": {"enum": ["PROVEN", "UNVERIFIED"]},
                "unverified": {"type": "array"},
            },
        }
        self.assertIsNone(structured_verdict_gate.structured_verdict_object([noise]))


class EvidenceResultChaosTests(unittest.TestCase):
    def test_nested_nonzero_exit_can_never_become_success(self):
        shapes = [
            {"exitCode": 1},
            {"result": {"return_code": 7}},
            {"tool": [{"status-code": 12}]},
            {"outer": {"inner": [{"returnCode": 255}]}},
        ]
        for shape in shapes:
            with self.subTest(shape=shape):
                reason = evidence_event_result._nonzero_exit(shape)
                self.assertTrue(reason.startswith("nonzero exit code "))

    def test_zero_exit_noise_does_not_create_false_failure(self):
        shapes = [
            {"exitCode": 0},
            {"result": {"return_code": "0"}},
            {"nested": [{"status_code": 0}, {"other": "value"}]},
        ]
        for shape in shapes:
            with self.subTest(shape=shape):
                self.assertEqual(evidence_event_result._nonzero_exit(shape), "")

    def test_malformed_exit_code_is_fail_open_not_fabricated_nonzero(self):
        self.assertEqual(evidence_event_result._nonzero_exit({"exit_code": "not-a-number"}), "")


if __name__ == "__main__":
    unittest.main()
