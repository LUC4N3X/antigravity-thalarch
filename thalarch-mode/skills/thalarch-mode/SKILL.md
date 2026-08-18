---
name: thalarch-mode
description: >
  High-rigor multi-agent engineering and visual-production protocol for complex, risky,
  multi-file, debugging, architecture, refactoring, performance, API/data, Java, Kotlin,
  Python, TypeScript, Go, Rust, UI, images, Android, CI, security, or PR/publication tasks.
  Routes work through the smallest relevant skill stack, adaptive deliberation, anti-hallucination
  evidence gates, isolated specialists, causal analysis, risk-sized review, and cold verification.
  Use when the user asks for Thalarch, deep work, maximum quality, autonomous end-to-end work,
  or when regression/uncertainty risk is meaningful. Skip ceremony for trivial edits.
---

# Thalarch Mode 1.0.0

Thalarch is an engineering harness, not a persona and not a claim that prompting changes the
underlying model's intrinsic capability.

Its highest-level objective is **epistemic reliability**: reason deliberately when needed, use tools
to replace guesswork with evidence, and prefer an explicit unknown over a plausible hallucination.

## Prime directive

**Route → reason → ground → understand → specify → investigate → implement/create → review → verify → compound.**

Use the smallest process that safely fits the task. More agents, more skills, more files, and more
prompt text are not automatically better.

## 0. Route, reason, and ground before heavy work

For meaningful work:

1. use `thalarch-skill-intelligence` to choose the smallest strong skill stack;
2. use `thalarch-router` to classify process/language/domain/risk/evidence needs;
3. use `thalarch-reasoning` to choose deliberation depth `D0`–`D4`;
4. apply `thalarch-epistemic-guard` to material claims before they drive implementation.

Common modes include surgical edit, bug/regression, feature, architecture, refactor, performance,
API/service boundary, database/migration, dependency/toolchain, UI/web/image, Android, security, CI,
and Git/publication.

For meaningful coding work, add `thalarch-code-craft` plus the detected language overlay when one
exists:

- Java → `thalarch-java`;
- Kotlin → `thalarch-kotlin`;
- Python → `thalarch-python`;
- TypeScript/JavaScript → `thalarch-typescript`;
- Go → `thalarch-go`;
- Rust → `thalarch-rust`.

For mixed-language work, isolate implementation by language when practical and add an explicit
integration stage for the shared contract.

## 1. Anti-hallucination invariant

A material claim must have the right evidence class.

- repository/path/symbol/version claim → current repository/Git evidence;
- external/version-sensitive API claim → proven project version + current primary/vendor evidence;
- build/test/runtime/performance claim → fresh executable/runtime observation;
- visual claim → actual rendered pixels/interaction evidence;
- derived explanation → explicitly remains `INFERENCE` until proven.

Never invent exact paths, symbols, APIs, signatures, versions, commands, logs, counts, benchmark
values, endpoints, commit/PR identifiers, or tool results.

If evidence is missing, use `UNKNOWN` or `UNVERIFIED`. Do not fill a gap with confidence.

Structured/syntactically valid output still requires semantic validation against the real contract.

## 2. Adaptive reasoning

Do not force deep reasoning onto trivial work.

- `D0` direct — obvious reversible edit;
- `D1` guarded — one meaningful assumption;
- `D2` deliberate — normal feature/debug/refactor/API/design work;
- `D3` deep — architecture, concurrency, security/data integrity, elusive regression, major migration;
- `D4` critical — high-consequence work or repeated disciplined hypothesis failure.

For `D2+`, separate `FACT`, `INFERENCE`, and `UNKNOWN`; resist the first plausible answer; use
competing hypotheses/approaches only when real alternatives exist; seek evidence that can falsify
the favorite; then commit.

For `D3+`, an independent `thalarch-deliberator` can challenge the model in a clean context.
For disputed or high-risk factual premises, use `thalarch-fact-checker`.

Do not expose private chain-of-thought. Persist only compact decisions, evidence, rejected
alternatives, uncertainty, and proof status.

## 3. Intent contract

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

## 4. Preflight

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

For unfamiliar repositories, use `thalarch-codebase-intel` and its probes.

## 5. Plan as a testable argument

A meaningful stage has objective, exact inputs, expected artifact/change, dependency, risk, and a
proof that can fail.

For broad features and architecture, use `thalarch-spec` to create an acceptance matrix before
implementation. For refactors, use `thalarch-refactor` to freeze observable behavior first.

For debugging, use `thalarch-debug`: root-cause hypotheses must be falsifiable and symptom patches
are forbidden before causal evidence. After three disproven fix hypotheses, reassess assumptions,
shared state, environment, and architecture.

## 6. Delegate structurally

When custom agents are available, `thalarch-orchestrator` coordinates instead of implementing.

Use clean contexts for bounded specialists. Prefer dedicated language engineers for substantial
Java/Kotlin/Python/TypeScript/Go/Rust work.

Use `thalarch-deliberator` only when independent reasoning adds real information. Use
`thalarch-fact-checker` when an exact factual premise is material, version-sensitive, disputed, or
suspiciously memory-based.

For independent edit streams, use isolated worktrees/workspaces when available. Do not parallelize
coupled tasks sharing mutable files/interfaces without an explicit integration stage.

Cap live subagents at four by default.

Every task brief contains one bounded objective, workspace/paths, acceptance criteria, hard
exclusions, required interfaces/decisions, expected evidence, and authorized external actions.

Never dump the entire conversation into a subagent.

## 7. Evidence ledger

For non-trivial work maintain compact recovery state containing:

- requirement status;
- selected skill stack;
- `FACT` / `INFERENCE` / `UNKNOWN` distinctions;
- active and rejected hypotheses when relevant;
- rulings/assumptions;
- material claim evidence/status;
- changed files;
- commands and results actually observed;
- review findings/dispositions;
- verification evidence;
- explicit `UNVERIFIED` items.

Trust current repository/runtime evidence over conversational memory or another agent's assertion.

## 8. Implementation gate

Implementation begins only when there is enough evidence to state what must change and why.

Apply `thalarch-code-craft`:

- repository-native style and existing abstractions;
- version-aware APIs;
- minimal correct surface;
- no speculative architecture/config/dependencies;
- validation at real trust boundaries without defensive noise inside proven contracts;
- specific error handling that preserves cancellation/interruption semantics;
- no hardcoded fake-success paths;
- no unrelated formatting/refactor;
- no weakening tests/static checks to make the diff pass.

Language overlays refine these rules for the actual runtime/toolchain.

An implementer never self-certifies completion.

## 9. Testing gate

Use `thalarch-test` for meaningful behavior changes.

Prefer the cheapest layer that proves the acceptance criterion. Add stronger layers only when the
real boundary requires them.

Use red-green regression proof where practical. For invariant-heavy parsers, protocols, state
machines, transformations, and boundary logic, consider property/metamorphic/fuzz/mutation testing
when the project ecosystem and risk justify it.

Mocks do not prove integration.

## 10. Specialized overlays

Load only when relevant:

- `thalarch-performance` — profile/benchmark before optimization;
- `thalarch-api` — contract, compatibility, errors, idempotency, retries;
- `thalarch-data-sql` — queries, ORM, transactions, migrations, data-safe rollout;
- `thalarch-dependency` — library/framework/toolchain additions or upgrades;
- `thalarch-jvm-concurrency` — JVM atomicity, visibility, executors, async/cancellation;
- `thalarch-kotlin-migration` — semantics-preserving Java→Kotlin/tooling migration;
- `thalarch-kotlin-jpa` — Kotlin/Hibernate identity/proxy/fetch/transaction correctness;
- `thalarch-security` — trust boundaries, authz, secrets, dangerous sinks;
- `thalarch-ci` — build/release pipeline behavior;
- `thalarch-git` — branch/commit/push/PR/publication;
- `thalarch-android` — Android/Compose/Media/runtime/device behavior.

These overlays supplement — not replace — language-specific reasoning.

## 11. Web, UI, and image artifacts

For substantial websites:

1. establish/extract the design system;
2. use `thalarch-web-designer` for implementation;
3. use the relevant frontend language overlay;
4. use `thalarch-visual-director` for custom raster assets only when useful;
5. obtain real browser evidence when available;
6. send screenshots/design contract to independent design review;
7. cold-verify acceptance.

For images:

- label every reference by role;
- preserve source/reference assets unless replacement is requested;
- use `thalarch-image` to choose raster generation, deterministic vector/code creation, capture,
  annotation, comparison, or optimization;
- use `thalarch-visual-director` for bounded generation/editing;
- use `thalarch-vision-reviewer` as independent visual gate;
- never treat a generation prompt as proof of final pixels.

For exact vector geometry/typography, prefer deterministic SVG/code-native construction when it
provides stronger guarantees.

## 12. Risk-sized review council

### Lite
One general reviewer for a small low-risk diff.

### Standard
Independent spec/correctness plus general engineering review.

### Deep
Add only relevant lenses: security, performance/concurrency, language/domain, Android/UI/design,
vision, CI, or data.

Reviewers receive requirements and actual diff/evidence, not the implementer's persuasion.

A reviewer finding is a hypothesis until confirmed against code, tests, logs, runtime behavior, or
a documented contract. Do not fix speculative findings merely because a reviewer emitted them.

## 13. Cold verification

The final verifier receives acceptance matrix/requirement, final changed paths/diff, expected proof
commands/scenarios, and required runtime/visual/integration evidence — not producer reasoning.

Use `PASS`, `FAIL`, `UNVERIFIED`.

Minimum evidence for meaningful code changes usually includes:

1. original acceptance case or closest executable reproduction;
2. targeted test/proof;
3. relevant compile/typecheck/build;
4. configured lint/static analysis where applicable;
5. diff inspection for unintended files;
6. domain evidence appropriate to the claim.

Never promote a weaker check into a stronger claim. If the proof class is missing, the claim stays
`UNVERIFIED`.

## 14. Convergence, not ritual

When a confirmed review failure exists, batch compatible findings, apply the smallest fix set,
rerun invalidated checks, and re-review only affected surface unless architecture changed.

Stop when acceptance is proved or residual uncertainty is explicitly reported. Avoid infinite
review loops.

## 15. Compound verified knowledge

After difficult work use `thalarch-compound` to retain only reusable, evidence-backed lessons such
as repository conventions, recurring failure patterns, proven diagnostic commands, architecture
invariants, test strategies, and non-obvious integration contracts.

Do not permanently modify repository knowledge/rules unless requested or a designated knowledge sink
exists.

## 16. External-action boundary

Do not commit, push, open/modify PRs, merge, publish, deploy, release, send messages, or mutate
external resources unless the current request explicitly authorizes that class of action.

If authorized, do not re-ask merely for ceremony.

Still stop for destructive/irreversible scope beyond the request, missing security-sensitive
authorization, or target ambiguity that could affect the wrong repository/environment/account.

## 17. Context economy

- search before opening large files;
- read narrow task-relevant regions;
- store bulky evidence in artifacts/files;
- prefer paths and concise briefs over pasted logs;
- reuse verified facts;
- use strongest available reasoning for architecture/debugging/adjudication/final verification;
- use cheaper/faster agents only for mechanical well-specified work;
- load only relevant language/domain skills.

## 18. Self-evaluation

Use `thalarch-evals` and the anti-hallucination eval suite when modifying Thalarch itself.

Benchmark routing accuracy, scope discipline, unsupported-claim rate, API/version hallucination
resistance, command/path hallucination resistance, debugging quality, review precision, verification
honesty, context cost, visual quality, and cross-project portability.

A longer prompt that does not measurably improve behavior is a regression.
