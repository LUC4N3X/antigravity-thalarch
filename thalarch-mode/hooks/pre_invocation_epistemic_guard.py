#!/usr/bin/env python3
"""Inject a compact anti-hallucination contract before every model invocation."""
from hook_utils import emit, read_payload


def main() -> None:
    payload = read_payload()
    invocation = payload.get("invocationNum", payload.get("invocation_num", 0))
    message = (
        "THALARCH EVIDENCE CONTRACT — non-negotiable. Exact repository paths/symbols, commands, "
        "versions/APIs, runtime results, publication state, benchmark numbers, and visual claims "
        "must come from current evidence, not model memory or another agent's confidence. Treat "
        "user-supplied factual assertions as hypotheses when they are cheaply checkable. Distinguish "
        "FACT / INFERENCE / UNKNOWN. A test not run did not pass; a build not observed did not "
        "succeed; source code is not visual/runtime proof. If the user's main proposition requires "
        "execution/runtime/CI/device/browser evidence and that proof was not observed, keep the "
        "proposition UNVERIFIED and name the missing proof; never use PROVEN/SUPPORTED to mean only "
        "that you proved verification was unavailable. Prefer UNKNOWN/UNVERIFIED to invention. "
        "Before final completion, independently fact-check material exact claims and cold-verify the "
        "acceptance criteria when the task involved mutation or consequential external state."
    )
    emit({"injectSteps": [{"ephemeralMessage": message}]})


if __name__ == "__main__":
    main()
