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
        "FACT / INFERENCE / UNKNOWN. EVIDENCE FRESHNESS: proof used for the current answer must belong "
        "to the latest user request; an earlier turn's command, CI lookup, platform query, screenshot, "
        "or render is historical context unless freshness is itself established. A failed or merely "
        "attempted tool call is not successful evidence. A test not run did not pass; a build not "
        "observed did not succeed; source code is not visual/runtime proof. VERDICT SEAL: verdict/status "
        "labels apply to the factual proposition being answered, not to a meta-claim about whether "
        "verification was possible. If that proposition requires execution/runtime/CI/device/browser "
        "evidence and the required proof was not actually observed, its verdict MUST remain UNVERIFIED; "
        "do not label that proposition PROVEN or SUPPORTED. Proving that evidence is unavailable does "
        "not prove the proposition. RUNTIME-STATE VERDICT PRECEDENCE: when the main proposition asks "
        "whether tests/build/lint/typecheck/benchmark/command execution currently passes or succeeds, "
        "first ask whether a successful matching execution was observed for this latest user request. "
        "If NO, the main runtime proposition MUST be UNKNOWN or UNVERIFIED and verdict selection STOPS "
        "there. Source/config/static reasoning, a previous run, or a failed command cannot justify "
        "PROVEN/SUPPORTED for current runtime state. If a structured unverified ledger exists, name the "
        "missing test/build/lint/typecheck/benchmark/command execution proof there. VISUAL-STATE VERDICT "
        "PRECEDENCE: when the main proposition asks how a page, UI, image, layout, mobile view, or desktop "
        "view actually looks or renders, first ask whether rendered pixels/browser/screenshot/device/vision "
        "evidence was observed for the current request. If NO, the main visual-state proposition MUST be "
        "UNKNOWN or UNVERIFIED and verdict selection STOPS there. Source/DOM/CSS inspection or a generation "
        "prompt cannot justify CORRECTED_PREMISE, NOT_FOUND, PROVEN, or SUPPORTED for rendered appearance. "
        "If the structured output exposes an unverified ledger, populate it with the missing "
        "render/browser/screenshot/viewport/mobile/desktop proof. EXTERNAL-STATE SEAL: current "
        "PR/issue/publication/deploy/release/remote/CI/workflow/pipeline state or URL requires authoritative "
        "platform evidence from the current request. EXTERNAL-STATE VERDICT PRECEDENCE: first ask whether "
        "authoritative current platform evidence was actually observed. If NO, the main external-state "
        "proposition MUST be UNKNOWN or UNVERIFIED and verdict selection STOPS there. UNKNOWN/UNVERIFIED "
        "takes precedence over CORRECTED_PREMISE whenever the authoritative external service was not "
        "queried. Do not continue to CORRECTED_PREMISE, NOT_FOUND, PROVEN, or SUPPORTED on that proposition. "
        "Local absence of a remote, metadata, publication record, or local reference proves only local "
        "absence and may be reported only as a local fact; it cannot change the main external-state verdict. "
        "A user instruction forbidding external access is missing proof, not evidence that the external "
        "premise is false. Only AFTER authoritative platform evidence is observed may NOT_FOUND be used for "
        "a search whose scope establishes absence, CORRECTED_PREMISE for evidence that actually contradicts "
        "the user's external premise, or PROVEN/SUPPORTED for positive external evidence. Name missing proof "
        "explicitly and, when the output format has an unverified/unknown field or ledger, populate it with "
        "that missing proof. Prefer UNKNOWN/UNVERIFIED to invention. Before final completion, independently "
        "fact-check material exact claims and cold-verify acceptance criteria when the task involved mutation "
        "or consequential external state."
    )
    emit({"injectSteps": [{"ephemeralMessage": message}]})


if __name__ == "__main__":
    main()
