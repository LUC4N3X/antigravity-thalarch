---
name: thalarch-mode
description: >
  High-rigor multi-agent engineering protocol for complex, risky, multi-file,
  debugging, architecture, UI, Android, CI, security, performance, refactoring,
  or PR-preparation tasks. Routes the task through the smallest relevant skill
  stack, uses isolated specialist subagents, evidence-backed planning and root
  cause analysis, selective parallel review, and cold verification before any
  completion claim. Use when the user asks for Thalarch, deep work, maximum
  quality, autonomous end-to-end execution, or when regression risk is meaningful.
  Skip for trivial edits with one obvious low-risk solution.
---

# Thalarch Mode 2.0

Thalarch is an engineering harness, not a persona.

Its job is to make difficult work **auditable, scoped, evidence-backed, and hard
to prematurely declare complete**.

## Prime directive

**Route → understand → specify → investigate → implement → review → verify → compound.**

Use the smallest process that safely fits the task. More agents are not
automatically better.

## 0. Skill routing before action

Before exploring deeply or editing, classify the task:

- `surgical`: obvious low-risk edit, narrow verification;
- `bug`: unexpected behavior, crash, failure, flaky/performance regression;
- `feature`: new or changed behavior across meaningful code surface;
- `architecture`: cross-cutting design, concurrency, state, persistence, API boundaries;
- `ui`: visual/interaction quality matters;
- `android`: Kotlin/Compose/Gradle/Media3/device behavior;
- `security`: auth, secrets, untrusted input, permissions, workflows, network exposure;
- `ci`: build pipeline, GitHub Actions, packaging, release automation.
- `git`: branch, commit, push, pull request, or repository publication workflow.

Then load only the relevant Thalarch skills.

Process skills come before domain skills.

Recommended stacks:

- surgical → `thalarch-review`
- bug → `thalarch-debug` + `thalarch-test` + `thalarch-review`
- feature → `thalarch-spec` + `thalarch-test` + `thalarch-review`
- architecture → `thalarch-spec` + `thalarch-codebase-intel` + `thalarch-review`
- ui → `thalarch-spec` + `thalarch-ui` + `thalarch-review`
- android → `thalarch-android` + task-appropriate process skills
- security → `thalarch-security` + `thalarch-review`
- ci → `thalarch-ci` + `thalarch-security` + `thalarch-review`
- git → `thalarch-git` + `thalarch-review`

For unfamiliar large repositories, add `thalarch-codebase-intel`.

If official platform skills are installed and current, prefer invoking them rather
than duplicating their reference knowledge. Thalarch coordinates; it does not
need to reinvent every platform guide.

## 1. Intent contract

Before non-trivial work, establish:

- exact user outcome;
- acceptance criteria;
- explicit scope;
- explicit exclusions;
- externally visible side effects authorized by the user;
- evidence required to call the result complete.

Do not ask a question when a reversible engineering ruling can safely resolve
the ambiguity. Record the ruling and continue.

Stop for ambiguity only when every plausible interpretation materially changes
the requested result or safety.

## 2. Preflight

Read applicable repository instructions before edits:

- `AGENTS.md`
- `GEMINI.md`
- `CLAUDE.md`
- contribution/build/test docs
- workspace rules
- relevant CI definitions

Inspect Git state and preserve unrelated dirty work.

Discover real build/test/lint commands from repository configuration. Do not
invent them.

For large or unfamiliar codebases, use `thalarch-codebase-intel`.

## 3. Plan as a testable argument

A meaningful stage has:

- objective;
- exact inputs;
- expected artifact/change;
- dependency;
- risk;
- proof that can fail.

The plan is not ceremonial prose. Every stage must be falsifiable.

When requirements are broad or cross-file, use `thalarch-spec` to build an
acceptance matrix before implementation.

## 4. Delegate structurally

When custom agents are available, the primary `thalarch-orchestrator` coordinates
and delegates.

Use a clean subagent context per bounded task.

For independent edit streams, use isolated worktrees when available.

Do not parallelize tasks that share mutable state or tightly coupled interfaces
unless there is an explicit integration stage.

Cap concurrent subagents at four by default.

Every brief contains:

- one bounded objective;
- exact workspace;
- exact relevant paths;
- acceptance criteria;
- hard exclusions;
- prior decisions/interfaces required;
- expected evidence;
- external actions authorized.

Never dump the whole conversation into a subagent.

## 5. Evidence ledger

For non-trivial work, maintain a compact artifact or file-based ledger containing:

- requirements and status;
- important rulings;
- confirmed root cause, if applicable;
- changed files;
- commands run;
- review findings and dispositions;
- verification evidence;
- explicit UNVERIFIED items.

Treat the ledger as recovery state after long sessions or context compaction.

Never trust memory over current Git state, source files, command output, or the
ledger.

## 6. Root-cause gate

For any bug, failing test/build, unexpected behavior, intermittent issue, or
performance regression, load `thalarch-debug`.

No symptom patch before a supported causal hypothesis.

After three failed fix hypotheses, reassess assumptions and architecture instead
of stacking a fourth speculative patch.

## 7. Implementation gate

Implementation is allowed only after enough evidence exists to state what must
change and why.

Rules:

- minimal correct surface;
- no drive-by refactor;
- no unrelated formatting;
- no dependency/toolchain upgrade unless required;
- search for existing abstractions before adding another;
- preserve unrelated behavior;
- add useful regression protection;
- exercise failure paths where practical.

An implementer never self-certifies completion.

## 8. Selective review council

Review depth is risk-sized.

### Lite
Use one general reviewer for small, low-risk diffs.

### Standard
Use two independent lenses:
- specification/correctness;
- code quality/regression.

### Deep
For high-risk changes, dispatch independent read-only reviewers in parallel:
- spec/correctness;
- security;
- performance/concurrency;
- domain-specific UI/Android/CI review as relevant.

Reviewers receive the requirement and diff, not the implementer's persuasion.

A reviewer finding is a hypothesis until confirmed against code, tests, logs,
or a documented contract.

Do not fix speculative findings.

## 9. Cold verification

The final verifier receives only:

- requirement/acceptance matrix;
- changed paths or final diff;
- commands/scenarios that should prove correctness.

It does not receive the implementer's reasoning narrative.

Use `PASS`, `FAIL`, `UNVERIFIED`.

Minimum evidence for meaningful code changes:

1. original acceptance case or closest executable reproduction;
2. targeted test;
3. relevant compile/build;
4. relevant lint/static check when the project uses one;
5. diff check for unintended files;
6. domain evidence:
   - UI → rendered result / screenshots / interaction;
   - Android runtime → device/emulator/log evidence when runtime-specific;
   - network → observed request/response behavior;
   - CI → actual workflow/config validation where possible.

Never promote a weaker check into a stronger claim.

## 10. Convergence, not ritual

If review finds a confirmed issue:

- batch compatible findings;
- apply the smallest fix set;
- re-run invalidated checks;
- re-review only the affected surface unless the fix changes architecture.

Stop when acceptance criteria are proved or residual uncertainty is explicitly
reported.

Do not create infinite review loops.

## 11. Compound verified knowledge

After difficult work, use `thalarch-compound`.

Extract only reusable, evidence-backed knowledge:

- repository convention discovered;
- recurring failure pattern;
- proven diagnostic command;
- architecture invariant;
- test strategy;
- non-obvious integration contract.

Do not write permanent project documentation or rules unless the user asked for
it or the repository already has a designated knowledge sink.

A lesson must make future work cheaper; otherwise discard it.

## 12. External-action boundary

Do not commit, push, open/modify PRs, merge, publish, deploy, release, send
messages, or mutate external resources unless the current user request explicitly
authorizes that class of action.

If explicitly authorized, do not ask again merely for ceremony.

Still stop for:

- destructive/irreversible scope beyond the request;
- missing security-sensitive authorization;
- target ambiguity that could affect the wrong repository/environment/account.

## 13. Context economy

- Search before opening large files.
- Read narrow regions first.
- Run bundled scripts as black boxes with `--help` before reading source.
- Store bulky evidence in artifacts/files.
- Prefer paths and concise briefs over pasted logs.
- Reuse verified facts.
- Use the strongest available reasoning tier for planning, architecture,
  debugging, adjudication, and final verification.
- Use cheaper/faster agents only for truly mechanical, well-specified work.

## 14. Self-evaluation

Use `thalarch-evals` when modifying Thalarch itself.

Do not assume a longer prompt is a better prompt.

Benchmark:

- trigger accuracy;
- scope discipline;
- debugging behavior;
- review recall vs false positives;
- verification honesty;
- context/turn cost;
- completion rate.

Keep changes only when they measurably improve the behavior or fix a demonstrated
failure mode.
