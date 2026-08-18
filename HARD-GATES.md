# Thalarch 1.0.0 — Hard Anti-Hallucination Gates

Thalarch treats hallucination resistance as a structural property, not a reminder such as
"be careful" or "double-check your answer".

The default plugin configuration enables four Antigravity hook-based evidence gates. They use
Antigravity's official `PreInvocation`, `PreToolUse`, and `Stop` lifecycle events and require
Python 3.10+.

## Why hooks exist

Prompt instructions can be forgotten, diluted by long context, or overridden by premature model
confidence. Hooks sit outside the model response and can interrupt an action or prevent the agent
from stopping.

The gates deliberately enforce only claims that can be checked with high confidence. If a hook
cannot reliably determine truth from the current workspace/transcript, it fails open and leaves the
claim to Thalarch's fact-checker/verifier rather than inventing a block.

## 1. Pre-invocation epistemic contract

`hooks/pre_invocation_epistemic_guard.py`

Before every model call, Antigravity injects a compact transient contract:

- exact paths and symbols come from repository evidence;
- project commands come from repository configuration;
- versions and external APIs are version-checked;
- tests/builds/runtime/publication states are never claimed without observation;
- source code is not visual/runtime proof;
- user-supplied factual assertions remain hypotheses when cheaply checkable;
- unsupported material claims are `UNKNOWN` or `UNVERIFIED`.

This message is intentionally compact so reliability does not require a large permanent prompt.

## 2. Exact read-target gate

`hooks/read_target_gate.py`

Before an exact `view_file` / `read_file` request, Thalarch checks that the requested local target
exists in the mounted workspace.

If it does not exist, the read is denied and the agent is instructed to search/list the repository
first.

This converts a common failure mode:

> "The implementation is in `src/foo/Bar.kt`" → attempts to read invented path

into:

> search repository → discover actual path → read actual file → make claim

Wildcard/discovery reads and unknown future Antigravity payload shapes are not blindly blocked.

## 3. Project-command grounding gate

`hooks/command_grounding_gate.py`

Before `run_command`, Thalarch checks high-confidence project facts such as:

- declared working directory exists;
- `gradlew` / `mvnw` wrapper exists before using it;
- an `npm` / `pnpm` / `yarn` script exists before calling an exact project script name;
- a referenced local Python/Node/shell/PowerShell script exists;
- an explicit Docker Compose file exists;
- ordinary Git commands run inside a detected Git repository.

The gate does **not** pretend to statically prove arbitrary shell semantics. Unknown commands are
allowed to execute and their real result becomes the evidence.

## 4. Stop evidence gate

`hooks/stop_evidence_gate.py`

This is the strongest gate.

Antigravity transcripts record model tool calls. When the Thalarch orchestrator delegated a real
mutation to an implementation specialist, the orchestrator is not allowed to finish until the
transcript shows fresh independent quality gates after the final mutation:

1. `thalarch-fact-checker` after the final mutation;
2. visual work → `thalarch-vision-reviewer` after the final visual generation/edit;
3. web-design work → `thalarch-design-reviewer` after the final web implementation;
4. `thalarch-verifier` after all applicable independent checks.

If any required check is missing, the Stop hook returns `continue`, forcing Antigravity back into
the execution loop with a system reason explaining what proof is missing.

The hook is enforced at the orchestrator boundary so implementation subagents do not deadlock while
waiting for reviewers they do not own.

### No infinite fake-success loop

If a required specialist is genuinely unavailable, Thalarch may stop only by saying that the
specific acceptance claim is **UNVERIFIED**. The hard gate prefers an honest incomplete result over
a fabricated PASS.

## Evidence hierarchy

Hard hooks complement, rather than replace, the normal Thalarch reasoning stack:

`repository/runtime evidence → official/current platform source → project rules → trusted specialist → model memory as hypothesis`

The model can still reason creatively. It simply cannot promote an inspectable guess into a fact
without evidence.

## What the gates intentionally cannot prove

No hook can make a language model literally incapable of hallucinating.

These gates reduce high-value failure modes, but semantic mistakes can still survive. For example:

- an existing API may still be used incorrectly;
- a passing test may assert the wrong contract;
- a reviewer may misinterpret a requirement;
- current documentation may be incomplete;
- runtime evidence may not cover every production condition.

That is why Thalarch still uses adaptive reasoning, independent fact checking, risk-sized review,
and cold verification.

## Validation

Run:

```bash
python validate_thalarch.py .
python validate_hard_gates.py .
```

`validate_hard_gates.py` checks the hook wiring, compiles every hard-gate script, and runs synthetic
regression tests for invented paths, invented package scripts, missing local scripts, unsupported
completion, visual-review ordering, and the explicit `UNVERIFIED` escape path.

## Disabling the hard gates

The hard gates are intentionally enabled by default. Advanced users can disable only the
`thalarch-epistemic-hard-gates` group in `thalarch-mode/hooks.json`, but doing so removes structural
anti-hallucination enforcement and leaves the corresponding behavior prompt-driven only.

The separate consequential/destructive-command confirmation hook remains disabled by default; it
serves a different purpose from epistemic reliability.
