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
        "succeed; source code is not visual/runtime proof. VERDICT SEAL: verdict/status labels apply "
        "to the factual proposition being answered, not to a meta-claim about whether verification "
        "was possible. If that proposition requires execution/runtime/CI/device/browser evidence and "
        "the required proof was not actually observed, its verdict MUST remain UNVERIFIED; do not "
        "label that proposition PROVEN or SUPPORTED. Proving that evidence is unavailable does not "
        "prove the proposition. EXTERNAL-STATE SEAL: current PR/issue/publication/deploy/release/remote "
        "state or URL requires authoritative platform evidence. Local absence of a remote, metadata, "
        "or publication record does not disprove an external object. If the authoritative external "
        "service was not queried, keep that external-state proposition UNKNOWN or UNVERIFIED; do not "
        "use CORRECTED_PREMISE, NOT_FOUND, PROVEN, or SUPPORTED merely from local absence. NOT_FOUND "
        "requires an authoritative search whose scope could establish absence. Name missing proof "
        "explicitly and, when the output format has an unverified/unknown field or ledger, populate "
        "it with that missing proof. Prefer UNKNOWN/UNVERIFIED to invention. Before final completion, "
        "independently fact-check material exact claims and cold-verify acceptance criteria when the "
        "task involved mutation or consequential external state."
    )
    emit({"injectSteps": [{"ephemeralMessage": message}]})


if __name__ == "__main__":
    main()
