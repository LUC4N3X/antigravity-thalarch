# Changelog

## 1.0.0 — Living release

Thalarch intentionally keeps the public version fixed at **1.0.0**. Capability changes are tracked
here and in Git history without semantic-version bumps.

### 2026-08-19 — Context, source grounding, doubt, and observability

- added `thalarch-context` for focused task packets, research isolation, context trust levels,
  stale-context recovery, and compact handoffs instead of conversation/repository flooding;
- added `thalarch-source-grounding` so load-bearing framework/library/runtime decisions prove the
  project's exact version and consult narrow current primary sources before implementation;
- source grounding treats retrieved documentation as technical evidence rather than instruction
  authority, preventing fetched-content prompt injection from expanding scope or authorizing tools;
- added `thalarch-doubt`, a bounded in-flight adversarial challenge for non-trivial D2+ decisions;
  reviewers receive artifact + contract rather than producer reasoning and findings are reconciled
  against evidence rather than rubber-stamped;
- added `thalarch-observability` for production-oriented structured logging, bounded-cardinality
  metrics, tracing/correlation, retries/queues/external integrations, telemetry privacy, and
  evidence-based alerting;
- strengthened `thalarch-code-craft` with vertical, contract-first, behavior-first, and risk-first
  evidence slices so uncertain multi-file work is falsified early instead of implemented in one
  large pass;
- added shortcut/rationalization defenses to the new reliability workflows while keeping them
  adaptive rather than inheriting universal numeric thresholds or mandatory ceremony;
- added `addyosmani/agent-skills` to Skill Intelligence's high-value discovery map without bundling
  or auto-installing the external skill pack;
- expanded Thalarch evals with source-grounding, fresh-context doubt, stale-context switching, and
  production observability cases;
- validator now requires the four new canonical reliability skills and their router/orchestrator
  wiring;
- public version remains permanently **1.0.0**.

### 2026-08-19 — Cross-model reliability benchmark

- added `benchmarks/` with a paired native-vs-Thalarch evaluation protocol for Antigravity/Gemini,
  Codex, and Claude Code;
- added 20+ adversarial engineering/design cases covering invented repository facts, nonexistent
  commands, false API/version premises, unrun tests, proof substitution, publication state,
  debugging, concurrency, Java/Kotlin/Python/TypeScript/Go/Rust, security, architecture, web/image
  fidelity, and external-action boundaries;
- added a version-controlled hallucination taxonomy/rubric and a result template that keeps task
  success separate from reliability;
- added `benchmarks/score_run.py` for host summaries and paired Thalarch deltas;
- added `validate_benchmarks.py` and wired benchmark validation/scorer smoke tests into CI;
- benchmark policy explicitly treats an honest `UNVERIFIED` as preferable to fabricated PASS.

### 2026-08-19 — Multi-engine adapters

- generalized Thalarch from an Antigravity-only presentation into one canonical model-agnostic
  engineering/reliability core with thin host-native adapters;
- refactored canonical skill intelligence, core orchestration, image generation/routing and browser
  QA to capability-detect the current host instead of assuming Antigravity-only agents/tools;
- added validator rules that reject known host-specific assumptions from canonical skills copied to
  every host;
- added an OpenAI Codex adapter using Agent Skills locations, `AGENTS.md` guidance, Codex-native
  lifecycle hooks and native custom `thalarch_deliberator`, `thalarch_fact_checker`, and
  `thalarch_verifier` agents;
- Codex specialist agents use high reasoning effort and non-editing/read-only sandbox configuration;
- strengthened the Codex evidence gate so a verification counts only when the tool response provides
  an explicit success signal; a check older than the final mutation or followed by a failed/unproven
  check cannot support completion;
- added an Anthropic Claude Code adapter using `.claude/skills`, `CLAUDE.md` guidance, Claude-native
  lifecycle hooks and independent deliberator/fact-checker/verifier subagents;
- Claude specialists use `model: inherit`, `effort: high`, and normal permission mode so the adapter
  remains portable while allowing real evidence-gathering commands; they are non-editing by
  instruction rather than unusable `plan`-mode shells;
- Claude `PostToolUseFailure` is tracked so a later failed verification invalidates earlier success;
- all host completion gates require verification that is both **successful and newer than the final
  relevant mutation**;
- added `installers/install_adapter.py` for cross-platform user/repository installation while
  preserving existing host/project instructions and hook configuration;
- existing Thalarch skills/agents are backed up before replacement; existing `AGENTS.md`,
  `CLAUDE.md`, Codex `hooks.json` and Claude `settings.json` are never overwritten by the adapter
  installer;
- removed stale hand-maintained `MANIFEST.txt`; Git tree plus executable validators are now the
  source of truth for distributed structure;
- expanded `validate_adapters.py` with syntax/config/TOML/frontmatter checks, host-neutral-core
  checks, fresh-successful-evidence ordering regressions, failed-verification invalidation, and
  temporary-repository installer smoke tests;
- public version remains permanently **1.0.0** across all hosts.

### 2026-08-18 — Hard anti-hallucination enforcement

- enabled a default `thalarch-epistemic-hard-gates` hook group using Antigravity `PreInvocation`,
  `PreToolUse`, and `Stop` lifecycle events;
- added a compact pre-invocation evidence contract so exact paths/symbols, commands, versions/APIs,
  runtime results, publication state and visual claims must come from current evidence;
- added a read-target gate that denies exact local `view_file`/`read_file` requests when the target
  does not exist, forcing repository discovery instead of invented paths;
- added a project-command grounding gate for repository wrappers, package scripts, local script
  paths, Docker Compose files, Git workspaces and declared working directories;
- added a transcript-backed Stop gate that blocks orchestrated completion after mutation until
  independent fact checking, applicable design/vision review, and a final cold verifier occur in
  the correct order;
- hard completion can escape unavailable specialist tooling only by preserving the affected claim
  as explicit `UNVERIFIED`, preventing infinite loops without permitting fake PASS results;
- added `validate_hard_gates.py` plus synthetic hook regression tests and wired them into CI;
- installers now require Python 3.10+ because the hard evidence gates are executable Python hooks;
- added `HARD-GATES.md` documenting behavior, evidence boundaries and intentional limitations.

### 2026-08-18 — Adaptive reasoning and anti-hallucination core

- added `thalarch-reasoning` with adaptive deliberation depths `D0`–`D4`, first-answer resistance,
  hypothesis/alternative tournaments, disconfirmation, independent adjudication and compact
  reasoning-state recovery without exposing private chain-of-thought;
- added `thalarch-deliberator`, a clean-context read-only specialist for high-uncertainty or
  high-risk decisions;
- added `thalarch-epistemic-guard` as a first-class evidence gate for repository, API/version,
  runtime, external-fact, visual and inferred claims;
- added `thalarch-fact-checker`, an independent exact-claim verifier that returns
  `PROVEN/SUPPORTED/INFERENCE/UNKNOWN/UNVERIFIED/DISPROVEN`;
- orchestrator now treats epistemic reliability as the primary quality objective and selects
  deliberation depth based on actual risk/uncertainty rather than always using maximum ceremony;
- verifier now audits paths, symbols, versions, APIs, commands, test/build results, benchmark values
  and publication state for unsupported claims before granting PASS;
- added adversarial hallucination evals for invented files/symbols, nonexistent Gradle tasks,
  user-supplied false versions, unrun tests, local-build→CI proof substitution, API-memory errors,
  source-only visual claims, disputed reviewer facts and fabricated commit/PR identifiers;
- validator now structurally requires the reasoning, epistemic, deliberator and fact-checker wiring.

### 2026-08-18 — Autonomous skill intelligence

- added `thalarch-skill-intelligence` so the orchestrator can inspect available skills by
  name/description and choose the smallest high-value compatible stack automatically;
- added authority/currentness, project specificity, version compatibility, tool/evidence leverage,
  redundancy, conflict and context-cost selection criteria;
- added re-routing after project discovery so irrelevant skills can be dropped and more specific
  ones activated;
- added a known-high-value source map for official Kotlin/JetBrains skills and selected community
  Java/JVM, design and engineering skill ecosystems;
- explicitly prevents skill soup, fabricated skill/agent/tool names and silent third-party
  installation.

### 2026-08-18 — Polyglot engineering

- added project-aware specialists for Java, Kotlin, Python, TypeScript/JavaScript, Go and Rust;
- added `thalarch-code-craft` for repository-native coding, minimal diffs, dependency discipline and
  version-sensitive API verification;
- upgraded the project probe with language/toolchain discovery;
- added deterministic `change_probe.py` for diff-language/risk-lens routing signals;
- added behavior-preserving refactoring, API, data/SQL and dependency/toolchain engineering skills.

### 2026-08-18 — JVM and Kotlin depth

- added `thalarch-jvm-concurrency` for atomicity, visibility, locks, executors, futures, virtual
  threads, framework-managed async, cancellation and deterministic concurrency verification;
- added `thalarch-kotlin-migration` with framework detection and staged semantic-preservation
  invariants for Java→Kotlin and Kotlin/tooling migration;
- added `thalarch-kotlin-jpa` for Kotlin-specific entity identity, equality, proxying, fetch,
  transaction and uniqueness correctness;
- router now prefers exact installed official Kotlin/JetBrains skills for current Kotlin platform
  facts when they match the proven task.

### 2026-08-18 — Architecture, testing and performance

- added `thalarch-architecture` with quality-attribute-driven decisions, alternative/tradeoff
  analysis, dependency/data-boundary review and evolutionary migration planning;
- expanded `thalarch-test` with boundary matrices, property/metamorphic testing, fuzzing,
  concurrency testing and risk-based mutation testing;
- mutation testing deliberately has no universal score target and is used only when it adds
  meaningful evidence;
- strengthened performance engineering with local/CI, debug/release, cold/warm/incremental/no-op
  build classification and same-workload comparison;
- strengthened review with contract-before-body, consumer-first, failure-first, bottom-up and
  removal-test perspective shifts without forcing reviewers to invent findings.

### 2026-08-18 — Creative engineering

- added semantic design-system extraction/creation;
- added production website design and implementation workflow;
- added `thalarch-image-to-code` for screenshot/mockup/reference-driven frontend fidelity;
- added visual/image task routing, native image generation/editing and independent visual review;
- added browser QA with real screenshots, interaction, console and network evidence;
- added deterministic image metadata and before/after comparison helpers;
- added a Design Read plus qualitative variance/motion/density calibration before visual work;
- strengthened anti-template design discipline while preserving accessibility, brand and existing
  project constraints.

### 2026-08-18 — Structural verification

- Antigravity orchestrator remains unable to directly edit project files, run shell commands or
  generate images;
- implementation, image generation, specialist review and cold verification remain structurally
  separated as far as each host's native capabilities permit;
- validators check specialist wiring, image-tool delegation, portable paths, advanced skill files,
  autonomous skill intelligence, adaptive reasoning, epistemic guard, independent fact checking,
  host adapters, and the permanent 1.0.0 version policy;
- Antigravity epistemic hard gates are enabled by default; the separate consequential/destructive-
  command confirmation hook remains disabled by default.
