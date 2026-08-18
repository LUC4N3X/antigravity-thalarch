# Changelog

## 1.0.0 — Living release

Thalarch intentionally keeps the public version fixed at **1.0.0**. Capability changes are tracked
here and in Git history without semantic-version bumps.

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

- added `thalarch-skill-intelligence` so the orchestrator can inspect available Antigravity skills
  by name/description and choose the smallest high-value compatible stack automatically;
- added authority/currentness, project specificity, version compatibility, tool/evidence leverage,
  redundancy, conflict and context-cost selection criteria;
- added re-routing after project discovery so irrelevant skills can be dropped and more specific
  ones activated;
- added a known-high-value source map for official Kotlin/JetBrains skills and selected community
  Java/JVM, design and engineering skill ecosystems;
- explicitly prevents skill soup, fabricated skill names and silent third-party installation.

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

- orchestrator remains unable to directly edit project files, run shell commands or generate
  images;
- implementation, image generation, specialist review and cold verification remain structurally
  separated;
- validator checks specialist wiring, image-tool delegation, portable paths, advanced skill files,
  autonomous skill intelligence, adaptive reasoning, epistemic guard, independent fact checking,
  and the permanent 1.0.0 version policy;
- epistemic hard gates are enabled by default; the separate consequential/destructive-command
  confirmation hook remains disabled by default.
