---
name: thalarch-mode
description: >
  Runs a high-rigor software engineering workflow for complex, risky, multi-file,
  debugging, refactoring, UI, architecture, or PR-preparation tasks. Uses staged
  planning, Antigravity subagents, root-cause investigation, minimal scoped edits,
  adversarial code review, and fresh verification evidence before completion.
  Use when the user asks for deep work, maximum quality, systematic handling,
  autonomous end-to-end execution, or when a task has meaningful regression risk.
  Do not use for trivial one-line edits or simple factual questions.
---

# Thalarch Mode

Thalarch Mode is a coordination protocol for serious engineering work. It improves
execution discipline; it does not magically change the base model's intelligence.

## Prime directive

**Understand → plan → prove → implement → review → verify → report.**

Never jump from a symptom directly to a fix. Never call work complete because it
"looks right". Never widen scope merely because nearby code could be improved.

## Activation

If the current agent is `thalarch-orchestrator`, execute this protocol directly.
Do **not** invoke another `thalarch-orchestrator`.

Otherwise, for a task that qualifies for Thalarch Mode and when the custom agent is
available, invoke `thalarch-orchestrator` and give it:

- the user's exact goal;
- explicit scope and "do not touch" constraints;
- workspace/repository location;
- any already-known evidence;
- whether external side effects such as commit/push/PR were explicitly authorized.

If custom agents are unavailable, use the same protocol inline and clearly mark
which checks could not be independently delegated.

## Mode selection

Use the lightest path that still controls risk:

1. **Simple path** — one obvious edit, low regression risk:
   inspect → edit → targeted check → diff review.
2. **Bug path** — crash, failure, regression, intermittent behavior:
   debugger → confirmed root cause → implementer → reviewer → verifier.
3. **Feature path** — multi-file or behavior change:
   planner → implementer(s) → reviewer → verifier.
4. **High-risk path** — architecture, concurrency, auth/security, persistence,
   networking, build/release, broad refactor:
   planner + debugger/research as needed → isolated implementation →
   adversarial reviewer → cold verifier.
5. **UI path** — visual or interaction work:
   planner → implementer → visual/interaction evidence → reviewer → verifier.

Read only the relevant reference files below; do not preload all of them:

- Bug/failure: `references/debugging-protocol.md`
- Review/PR/change validation: `references/review-protocol.md`
- UI/UX/visual work: `references/ui-protocol.md`
- Android/Compose/Gradle work: `references/android-protocol.md`
- Efficiency/context control: `references/context-efficiency.md`

## Phase 0 — Preflight before touching code

1. Read repository instructions first:
   `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, README/contributing files, and
   relevant `.agents/rules` when present.
2. Establish Git state:
   current branch, dirty files, current diff, recent relevant commits.
3. Identify the project's real build/test/lint commands from repository files.
   Do not guess commands when the repo defines them.
4. Record exact scope:
   - requested outcome;
   - files/areas likely involved;
   - explicit exclusions;
   - external actions authorized by the user.
5. For non-trivial work, maintain a task/implementation-plan artifact as the
   source of truth. Re-read it after long tool sequences or context compaction.
6. Optional: run `python scripts/project_probe.py --path <workspace>` for a
   read-only project snapshot.

## Phase 1 — Build an evidence-backed plan

For meaningful work, the planner must produce stages. Every stage needs:

- **goal**
- **inputs**
- **expected output**
- **proof/check that can fail**
- **risk if wrong**
- **dependencies on other stages**

Separate independent tasks from tightly coupled tasks.

Parallelize only genuinely independent work. Prefer isolated worktrees for
parallel edits that may collide. Cap concurrent subagents at four.

A plan is allowed to change when evidence changes. Do not silently expand scope.

## Phase 2 — Investigate before editing

For bugs, failures, performance regressions, flaky behavior, build errors, or
unexpected results, root cause comes first.

Required evidence may include:

- exact reproduction;
- stack trace/error output;
- request/response or data-flow boundary evidence;
- git history/diff around the regression;
- comparison with a known-working path;
- a falsifiable hypothesis.

No "probably X, so let's patch X". If evidence is insufficient, gather more.

After three failed fix hypotheses, stop stacking patches. Reassess the design or
architecture with a fresh planner/debugger pass.

## Phase 3 — Implement with scope discipline

Implementation rules:

- Change the smallest surface that solves the confirmed problem.
- Preserve existing architecture and conventions unless the task explicitly
  requires architectural change.
- No drive-by refactors, mass formatting, dependency upgrades, renames, or
  cleanup unrelated to the requested result.
- Do not duplicate existing helpers or abstractions without first searching for
  the repository's established pattern.
- Keep behavior changes and refactors separable when possible.
- Add or update tests where they provide real regression protection.
- Exercise at least one failure/error path for behavioral changes when feasible.
- If a task says "only this", interpret it literally.

An implementer does not self-certify completion.

## Phase 4 — Review in two different lenses

### A. Specification review

Ask: **Did the change implement exactly the requested behavior and nothing else?**

Check every user requirement against actual code/diff/evidence.

### B. Engineering review

Ask: **Even if it matches the spec, is the implementation safe and maintainable?**

Check correctness, edge cases, error handling, lifecycle/state, concurrency,
performance, security/privacy, compatibility, tests, and project conventions.

For substantial work, use `thalarch-reviewer` as a separate read-only agent.

A finding is not real merely because a reviewer said it. Confirm it against the
actual code, test, log, or documented contract before changing code.

## Phase 5 — Cold verification

Use `thalarch-verifier` with **only**:

- the user's requirements/spec;
- the final diff or changed file paths;
- the commands that are supposed to prove correctness.

Do not give it the implementer's reasoning or "why this should work".

The verifier independently derives checks and runs them fresh.

Minimum completion evidence for code changes:

1. targeted test or reproduction of the original behavior;
2. relevant build/compile check;
3. relevant lint/static check when the project uses one;
4. diff inspection including unintended files;
5. fresh check of the original acceptance criteria.

Do not claim:
- "fixed"
- "build passes"
- "tests pass"
- "ready"
- "done"

without fresh evidence from this run.

If a check cannot be run, report it as **UNVERIFIED**, with the exact reason.

## Phase 6 — Delivery

Final report should be compact and operational:

- root cause or design decision;
- what changed;
- files changed;
- verification commands and actual results;
- remaining risk / unverified items;
- suggested professional commit message;
- external actions performed, if the user explicitly authorized them.

Do not hide failed checks.

## External side effects and stop conditions

Do not commit, push, open/modify a PR, merge, publish, deploy, release, delete
data, rotate secrets, or make other external/destructive changes unless the user
has explicitly authorized that class of action in the current task.

If the current task explicitly says to perform an external action, do not ask
again merely for ceremony. Stop only if:

- the operation is destructive/irreversible beyond the stated request;
- security-sensitive authorization is missing;
- the action affects a target outside the authorized scope;
- requirements are so contradictory that every implementation path is guesswork.

Otherwise make a defensible ruling, record it in the plan artifact, and continue.

## Context discipline

- Search before opening huge files.
- Read narrow line ranges first, then expand only when needed.
- Pass subagents file paths and concise briefs instead of dumping long logs.
- Keep bulky evidence in artifacts/files, not repeated in conversation.
- Use scripts as black boxes when possible; run `--help` before reading them.
- Reuse verified facts; do not repeatedly rediscover the same repository state.
- Prefer one high-quality subagent turn over many cheap, wandering turns.

## Quality bar

Thalarch Mode succeeds when the answer is not merely plausible but **auditable**:
the user can see what was changed, why, what proves it, and what is still unknown.
