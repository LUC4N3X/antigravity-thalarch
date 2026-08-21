from __future__ import annotations

import unittest
from unittest.mock import patch

import convergent_stop_gate as gate
from runtime_profile import classify_depth


class ConvergenceGuardTests(unittest.TestCase):
    def _payload_patches(self, *, verdict, old_state=None, calls=None):
        return (
            patch.object(gate, "latest_user_context", return_value=(0, "check tests", "req123")),
            patch.object(gate, "current_finish_values", return_value=[verdict]),
            patch.object(gate, "current_model_content", return_value=""),
            patch.object(gate, "structured_verdict_object", return_value=verdict),
            patch.object(gate, "transcript_call_rows", return_value=calls or []),
            patch.object(gate, "load_state", return_value=old_state or {}),
        )

    def test_first_honest_runtime_retry_is_preserved(self):
        verdict = {"conclusion": "UNVERIFIED", "unverified": ["Missing test suite execution output."]}
        delegated = {"decision": "continue", "reason": "THALARCH FRESH PROOF GATE: runtime test evidence missing"}
        patches = self._payload_patches(verdict=verdict)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, state = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "continue")
        self.assertEqual(state["attempts"], 1)

    def test_second_identical_honest_retry_stops_without_new_evidence(self):
        verdict = {"conclusion": "UNVERIFIED", "unverified": ["Missing test suite execution output."]}
        delegated = {"decision": "continue", "reason": "THALARCH FRESH PROOF GATE: runtime test evidence missing"}
        patches = self._payload_patches(verdict=verdict)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            _, first = gate.decide_convergence({}, delegated)
        patches = self._payload_patches(verdict=verdict, old_state=first)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, second = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "stop")
        self.assertEqual(second["attempts"], 2)
        self.assertIn("CONVERGENCE GUARD", decision["reason"])

    def test_new_tool_evidence_resets_convergence_attempt(self):
        verdict = {"conclusion": "UNVERIFIED", "unverified": ["Missing test execution proof."]}
        delegated = {"decision": "continue", "reason": "THALARCH FRESH PROOF GATE: runtime test evidence missing"}
        old = {"signature": "not-used", "attempts": 9, "nonterminal_count": 0}
        patches = self._payload_patches(verdict=verdict, old_state=old, calls=[(1, "view_file", "{}")])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, state = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "continue")
        self.assertEqual(state["attempts"], 1)
        self.assertEqual(state["nonterminal_count"], 1)

    def test_strong_verdict_never_uses_convergence_escape(self):
        verdict = {"conclusion": "PROVEN", "unverified": ["Missing test execution proof."]}
        delegated = {"decision": "continue", "reason": "THALARCH FRESH PROOF GATE: runtime test evidence missing"}
        patches = self._payload_patches(verdict=verdict, old_state={"attempts": 20})
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, state = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "continue")
        self.assertIsNone(state)

    def test_orchestration_block_is_never_bypassed(self):
        verdict = {"conclusion": "UNVERIFIED", "unverified": ["Missing verifier review."]}
        delegated = {"decision": "continue", "reason": "THALARCH HARD EVIDENCE GATE: cold verifier missing"}
        patches = self._payload_patches(verdict=verdict, old_state={"attempts": 20})
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, state = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "continue")
        self.assertIsNone(state)

    def test_visual_retry_requires_visual_missing_proof(self):
        verdict = {"conclusion": "UNVERIFIED", "unverified": ["Need more information."]}
        delegated = {"decision": "continue", "reason": "THALARCH VISUAL-STATE FINAL VERDICT GATE: rendered visual proof missing"}
        patches = self._payload_patches(verdict=verdict, old_state={"attempts": 20})
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            decision, state = gate.decide_convergence({}, delegated)
        self.assertEqual(decision["decision"], "continue")
        self.assertIsNone(state)


class AdaptiveProfileTests(unittest.TestCase):
    def test_critical_profile(self):
        self.assertEqual(classify_depth("Deploy this auth migration to production"), "D4")

    def test_deep_profile(self):
        self.assertEqual(classify_depth("Investigate a concurrency race condition"), "D3")

    def test_standard_profile(self):
        self.assertEqual(classify_depth("Fix this Python bug and add tests"), "D2")

    def test_direct_profile(self):
        self.assertEqual(classify_depth("Fix this README typo"), "D0")


if __name__ == "__main__":
    unittest.main()
