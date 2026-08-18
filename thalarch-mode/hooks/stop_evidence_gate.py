#!/usr/bin/env python3
"""Stop hook that prevents an orchestrated mutation from ending without cold evidence.

The gate reads Antigravity's transcript JSONL and reasons only over actual tool
calls recorded in PLANNER_RESPONSE.tool_calls. It does not infer that a tool ran
from prose. If required specialist tools are unavailable, the agent may exit only
by explicitly reporting the affected claim as UNVERIFIED instead of fabricating
completion.
"""
from __future__ import annotations

from typing import Any

from hook_utils import args_text, emit, latest_model_content, load_state, read_payload, save_state, tool_calls

MUTATING_TOOLS = {
    "write_to_file",
    "write_file",
    "edit_file",
    "replace_file_content",
    "multi_replace_file_content",
    "str_replace",
    "apply_patch",
    "create_file",
    "delete_file",
    "generate_image",
}

MUTATOR_AGENTS = {
    "thalarch-implementer",
    "thalarch-java-engineer",
    "thalarch-kotlin-engineer",
    "thalarch-python-engineer",
    "thalarch-typescript-engineer",
    "thalarch-go-engineer",
    "thalarch-rust-engineer",
    "thalarch-web-designer",
    "thalarch-visual-director",
}


def invoked_agent(args: dict[str, Any], agent_name: str) -> bool:
    return agent_name in args_text(args)


def unavailable_but_honest(content: str) -> bool:
    lowered = content.lower()
    return (
        "unverified" in lowered
        and any(token in lowered for token in ("unavailable", "could not invoke", "cannot invoke", "not available", "unable to invoke"))
    )


def main() -> None:
    payload = read_payload()
    if not bool(payload.get("fullyIdle", True)):
        emit({"decision": "stop"})
        return

    reason = str(payload.get("terminationReason") or "").lower()
    if reason in {"error", "max_steps_exceeded", "cancelled", "canceled", "user_cancelled", "user_canceled"}:
        emit({"decision": "stop"})
        return

    calls = tool_calls(payload)
    if not calls:
        emit({"decision": "stop"})
        return

    mutation_orders: list[int] = []
    visual_orders: list[int] = []
    web_orders: list[int] = []
    fact_orders: list[int] = []
    verifier_orders: list[int] = []
    vision_review_orders: list[int] = []
    design_review_orders: list[int] = []
    orchestrated_mutation = False

    for order, name, args in calls:
        lowered_name = name.lower()
        text = args_text(args)

        if lowered_name in MUTATING_TOOLS:
            mutation_orders.append(order)
            if lowered_name == "generate_image":
                visual_orders.append(order)

        if lowered_name == "invoke_subagent":
            for agent in MUTATOR_AGENTS:
                if agent in text:
                    orchestrated_mutation = True
                    mutation_orders.append(order)
            if "thalarch-visual-director" in text:
                visual_orders.append(order)
            if "thalarch-web-designer" in text:
                web_orders.append(order)
            if "thalarch-fact-checker" in text:
                fact_orders.append(order)
            if "thalarch-verifier" in text:
                verifier_orders.append(order)
            if "thalarch-vision-reviewer" in text:
                vision_review_orders.append(order)
            if "thalarch-design-reviewer" in text:
                design_review_orders.append(order)

    # This hard completion protocol is intentionally enforced at the orchestrator
    # boundary. Specialist subagents are allowed to return evidence to the parent;
    # otherwise each implementer would deadlock waiting for a verifier it cannot own.
    if not orchestrated_mutation:
        emit({"decision": "stop"})
        return

    last_mutation = max(mutation_orders)
    missing: list[str] = []

    last_fact = max(fact_orders) if fact_orders else -1
    if last_fact <= last_mutation:
        missing.append("independent fact-check after the final mutation")

    last_vision = max(vision_review_orders) if vision_review_orders else -1
    if visual_orders and last_vision <= max(visual_orders):
        missing.append("independent vision review after the final generated/edited visual asset")

    last_design = max(design_review_orders) if design_review_orders else -1
    if web_orders and last_design <= max(web_orders):
        missing.append("independent design review after the final web-design implementation")

    quality_gate_orders = [last_mutation, last_fact, last_vision, last_design]
    required_before_verifier = max(quality_gate_orders)
    last_verifier = max(verifier_orders) if verifier_orders else -1
    if last_verifier <= required_before_verifier:
        missing.append("cold verifier after all applicable fact/design/vision checks")

    if not missing:
        save_state(payload, "stop-evidence-gate", {"signature": "clear", "attempts": 0})
        emit({"decision": "stop"})
        return

    latest = latest_model_content(payload)
    if unavailable_but_honest(latest):
        # Honesty beats a fabricated PASS. The final answer must retain UNVERIFIED.
        emit({"decision": "stop"})
        return

    signature = f"{last_mutation}|{'|'.join(sorted(missing))}"
    state = load_state(payload, "stop-evidence-gate")
    attempts = int(state.get("attempts", 0)) + 1 if state.get("signature") == signature else 1
    save_state(payload, "stop-evidence-gate", {"signature": signature, "attempts": attempts})

    missing_text = "; ".join(missing)
    escalation = ""
    if attempts >= 3:
        escalation = (
            " If a required Thalarch specialist is genuinely unavailable, stop trying to fake the "
            "gate: state which proof could not be obtained and keep that acceptance claim explicitly "
            "UNVERIFIED in the final response."
        )

    emit({
        "decision": "continue",
        "reason": (
            "THALARCH HARD EVIDENCE GATE: completion is blocked because the final mutation is not "
            f"followed by the required independent evidence: {missing_text}. Do not claim DONE, "
            "PASS, fixed, visually correct, pushed/published, or regression-free yet. Run the missing "
            "independent checks using current evidence, then cold-verify the acceptance criteria."
            + escalation
        ),
    })


if __name__ == "__main__":
    main()
