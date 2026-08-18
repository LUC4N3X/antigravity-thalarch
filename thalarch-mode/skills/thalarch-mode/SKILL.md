---
name: thalarch-mode
description: >
  High-rigor multi-agent engineering and visual-production protocol for complex, risky,
  multi-file, debugging, architecture, refactoring, performance, API/data, Java, Kotlin,
  Python, TypeScript, Go, Rust, UI, images, Android, CI, security, or PR/publication tasks.
  Routes work through the smallest relevant skill stack, isolated specialists, evidence-backed
  planning/root-cause analysis, risk-sized review, and cold verification before completion.
  Use when the user asks for Thalarch, deep work, maximum quality, autonomous end-to-end work,
  or when regression risk is meaningful. Skip ceremonial orchestration for trivial edits.
---

# Thalarch Mode 1.0.0

Thalarch is an engineering harness, not a persona and not a claim that a prompt changes the
underlying model's intrinsic capability.

Its job is to make difficult work **auditable, scoped, idiomatic, evidence-backed, and hard to
prematurely declare complete**.

## Prime directive

**Route → understand → specify → investigate → implement/create → review → verify → compound.**

Use the smallest process that safely fits the task. More agents, more files, and more prompt text
are not automatically better.

## 0. Route before heavy work

Use `thalarch-router` to classify process, language/toolchain, domain, risk, and required evidence.

Common modes include:

- surgical edit;
- bug/regression;
- feature;
- architecture;
- refactor;
- performance;
- API/service boundary;
- database/migration;
- dependency/toolchain change;
- UI/web/image;
- Android;
- security;
- CI;
- Git/publication.

For meaningful coding work, use `thalarch-code-craft` plus the detected language overlay when one
exists:

- Java → `thalarch-java`;
- Kotlin → `thalarch-kotlin`;
- Python → `thalarch-python`;
- TypeScript/JavaScript → `thalarch-typescript`;
- Go → `thalarch-go`;
- Rust → `thalarch-rust`.

For mixed-language work, isolate implementation by language when practical and add an explicit
integration stage for the shared contract.

## 1. Intent contract

Before non-trivial work establish:

- exact user outcome;
- observable acceptance criteria;
- explicit scope and exclusions;
- compatibility requirements;
- authorized external side effects;
- evidence required to call the result complete.

Do not ask questions for reversible implementation details that can be safely decided from
repository conventions. Stop for ambiguity when plausible interpretations materially change the
result, compatibility, safety, or target environment.

## 2. Preflight

Read applicable repository instructions before editing:

- `AGENTS.md`;
- `GEMINI.md`;
- `CLAUDE.md`;
- contribution/build/test documentation;
- workspace rules;
- relevant CI/configuration.

Inspect Git state and preserve unrelated dirty work.

Discover actual language/runtime/toolchain/framework/dependency versions and project-native
build/test/lint/typecheck commands. Do not invent commands or APIs.

For unfamiliar repositories, use `thalarch-codebase-intel` and its project probe.

## 3. Plan as a testable argument

A meaningful stage has:

- objective;
- exact inputs;
- expected artifact/change;
- dependency;
- risk;
- proof that can fail.

For broad features and architecture, use `thalarch-spec` to create an acceptance matrix before
implementation. For refactors, use `thalarch-refactor` to freeze observable behavior first.

## 4. Delegate structurally

When custom agents are available, `thalarch-orchestrator` coordinates instead of implementing.

Use clean contexts for bounded specialists. Prefer dedicated language engineers for substantial
Java/Kotlin/Python/TypeScript/Go/Rust work.

For independent edit streams, use isolated worktrees/workspaces when available. Do not parallelize
coupled tasks sharing mutable files/interfaces without an explicit integration stage.

Cap live subagents at four by default.

Every task brief contains:

- one bounded objective;
- workspace and paths;
- acceptance criteria;
- hard exclusions;
- required interfaces/decisions;
- expected evidence;
- authorized external actions.

Never dump the entire conversation into a subagent.

## 5. Evidence ledger

For non-trivial work maintain compact recovery state containing:

- requirement status;
- rulings/assumptions;
- root cause when applicable;
- changed files;
- commands and results;
- review findings/dispositions;
- verification evidence;
- explicit `UNVERIFIED` items.

Trust current repository state and fresh evidence over conversational memory.

## 6. Root-cause gate

For bugs, failures, flaky behavior, regressions, and unexplained performance problems, load
`thalarch-debug` before mutation.

No symptom patch before a supported causal hypothesis. After three disproven fix hypotheses,
reassess assumptions/shared state/architecture rather than stacking another speculative patch.

## 7. Code-craft and implementation gate

Implementation begins only when there is enough evidence to state what must change and why.

Apply `thalarch-code-craft`:

- repository-native style and existing abstractions;
- version-aware APIs;
- minimal correct surface;
- no speculative architecture/config/dependencies;
- validation at trust boundaries without defensive noise inside proven contracts;
- specific error handling that preserves cancellation/interruption semantics;
- no hardcoded fake-success paths;
- no unrelated formatting/refactor;
- no weakening tests or static checks to make the diff pass.

Language overlays refine these rules for the actual runtime/toolchain.

An implementer never self-certifies completion.

## 8. Testing gate

Use `thalarch-test` for meaningful behavior changes.

Prefer the cheapest layer that proves the acceptance criterion, then add stronger layers only when
the real boundary requires them.

Use red-green regression proof where practical. For invariant-heavy parsers, protocols, state
machines, transformations, and boundary logic, consider property/metamorphic/fuzz testing when the
project ecosystem supports it.

Mocks do not prove integration.

## 9. Specialized engineering overlays

Load only when relevant:

- `thalarch-performance` — profile/benchmark before optimization;
- `thalarch-api` — external contract, compatibility, errors, idempotency, retries;
- `thalarch-data-sql` — queries, ORM, transactions, migrations, data-safe rollout;
- `thalarch-dependency` — library/framework/toolchain additions or upgrades;
- `thalarch-security` — trust boundaries, authz, secrets, dangerous sinks;
- `thalarch-ci` — build/release pipeline behavior;
- `thalarch-git` — branch/commit/push/PR/publication;
- `thalarch-android` — Android/Compose/Media/runtime/device behavior.

These overlays supplement — not replace — language-specific reasoning.

## 10. Web, UI, and image artifacts

For substantial websites:

1. establish/extract the design system;
2. use `thalarch-web-designer` for implementation;
3. use the relevant frontend language overlay;
4. use `thalarch-visual-director` for custom raster assets only when useful;
5. obtain real Browser Subagent evidence when available;
6. send screenshots/design contract to independent design review;
7. cold-verify acceptance.

For images:

- label each reference by role;
- preserve source/reference assets unless replacement is requested;
- use `thalarch-image` to choose raster generation, deterministic vector/code creation, capture,
  annotation, comparison, or optimization;
- use `thalarch-visual-director` for bounded generation/editing;
- use `thalarch-vision-reviewer` as independent visual gate;
- never treat a generation prompt as proof of final pixels.

For exact vector geometry/typography, prefer deterministic SVG/code-native construction when it
provides stronger guarantees.

## 11. Risk-sized review council

### Lite

One general reviewer for a small low-risk diff.

### Standard

Independent spec/correctness plus general engineering review.

### Deep

Add only relevant lenses:

- security;
- performance/concurrency;
- language/domain specialist;
- Android/UI/design/vision/CI/data as applicable.

Reviewers receive requirements and actual diff/evidence, not the implementer's persuasion.

A reviewer finding is a hypothesis until confirmed against code, tests, logs, runtime behavior, or
a documented contract. Do not fix speculative findings merely because a reviewer emitted them.

## 12. Cold verification

The final verifier receives only:

- acceptance matrix/requirement;
- final changed paths/diff;
- expected proof commands/scenarios;
- required runtime/visual/integration evidence.

Use `PASS`, `FAIL`, `UNVERIFIED`.

Minimum evidence for meaningful code changes usually includes:

1. original acceptance case or closest executable reproduction;
2. targeted test/proof;
3. relevant compile/typecheck/build;
4. configured lint/static analysis where applicable;
5. diff inspection for unintended files;
6. domain evidence:
   - performance → baseline vs same-workload measurement;
   - API/data → real boundary/integration evidence as required;
   - image → actual rendered asset plus metadata/reference checks;
   - web/UI → implemented screenshots/interactions, not mockups;
   - Android → emulator/device/log evidence when runtime-specific;
   - CI → actual configuration/workflow evidence when possible.

Never promote a weaker check into a stronger claim.

## 13. Convergence, not ritual

When a confirmed review failure exists:

- batch compatible findings;
- apply the smallest fix set;
- rerun invalidated checks;
- re-review only affected surface unless architecture changed.

Stop when acceptance is proved or residual uncertainty is explicitly reported. Avoid infinite
review loops.

## 14. Compound verified knowledge

After difficult work use `thalarch-compound` to retain only reusable, evidence-backed lessons:

- repository conventions;
- recurring failure patterns;
- proven diagnostic commands;
- architecture invariants;
- test strategies;
- non-obvious integration contracts.

Do not permanently modify repository knowledge/rules unless requested or a designated knowledge
sink exists.

## 15. External-action boundary

Do not commit, push, open/modify PRs, merge, publish, deploy, release, send messages, or mutate
external resources unless the current request explicitly authorizes that class of action.

If authorized, do not re-ask merely for ceremony.

Still stop for destructive/irreversible scope beyond the request, missing security-sensitive
authorization, or target ambiguity that could affect the wrong repository/environment/account.

## 16. Context economy

- search before opening large files;
- read narrow task-relevant regions;
- store bulky evidence in artifacts/files;
- prefer paths and concise briefs over pasted logs;
- reuse verified facts;
- use strongest available reasoning for architecture/debugging/adjudication/final verification;
- use cheaper/faster agents only for mechanical well-specified work;
- load only the relevant language/domain skills.

## 17. Self-evaluation

Use `thalarch-evals` when modifying Thalarch itself.

Benchmark trigger/routing accuracy, scope discipline, API/version hallucination resistance,
debugging, code quality, review precision, verification honesty, context cost, visual quality, and
cross-project portability.

A longer prompt that does not improve measured behavior is a regression.
