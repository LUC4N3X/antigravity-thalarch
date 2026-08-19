# High-value skill source map

This file is a **selection aid**, not a bundled dependency list. Thalarch should only activate a
skill if it is actually available in the current host session and matches the proven task.

Never fabricate these names, silently install them, or treat this file as stronger than repository
rules/current primary documentation.

## Production engineering lifecycle — community candidates

Repository family: `addyosmani/agent-skills`.

This collection is especially useful as a source of process mechanics rather than as a reason to
bulk-load its full catalog. High-value installed candidates include:

- `source-driven-development` — exact project-version detection plus current primary documentation
  before framework/library decisions;
- `doubt-driven-development` — bounded fresh-context adversarial challenge while important decisions
  are still cheap to change;
- `context-engineering` — focused context packets, research isolation, stale-context recovery and
  trust-level discipline;
- `incremental-implementation` — vertical/contract-first/risk-first implementation slices with
  verification between meaningful mutations;
- `observability-and-instrumentation` — operational questions mapped to structured logs, metrics,
  traces and actionable alerting;
- `browser-testing-with-devtools` — real browser evidence when compatible tooling exists;
- `code-simplification` — behavior-preserving simplification and respect for existing design intent.

Thalarch already contains canonical equivalents/derived mechanisms for several of these concerns.
Prefer an installed external skill only when it is more specific or exposes stronger host-native
tooling; do not load both merely because both are reputable.

Useful design lessons from this source family include process-over-prose, explicit exit evidence,
progressive disclosure, and shortcut/rationalization defenses. Thalarch keeps these adaptive rather
than inheriting universal numeric thresholds or mandatory commits/questions that may conflict with
the current user/repository contract.

## Autoresearch / bounded experiment loops — community candidates

Discovery index: `webfuse-com/awesome-autoresearch`.

High-value sources for experiment-loop mechanics include:

- `supratikpm/gemini-autoresearch` — Antigravity-compatible iterative research patterns;
- `junjunjunbong/research-loop` — isolated Git worktrees and explicit keep/revert experiment state;
- `uditgoenka/autoresearch` — one-change-at-a-time measurement discipline and rollback semantics;
- `sentient-agi/EvoSkill` — evidence-driven reusable-skill evolution from repeated failure patterns.

Thalarch does **not** vendor or blindly compose these projects. `thalarch-autoresearch` keeps only the
portable engineering mechanics that fit Thalarch's existing reliability contract: frozen baselines,
comparable measurement, bounded budgets, correctness-before-score guardrails, deterministic
KEEP/REVERT/INCONCLUSIVE decisions, isolated candidate work, benchmark-overfitting defenses, and a
strict boundary against silent self-modification or unauthorized publication.

Use external autoresearch skills only when they add host-native tooling or a task-specific evaluator
that Thalarch does not already provide. Do not stack multiple autonomous loops around the same mutable
workspace.

## Kotlin / JetBrains — official-source preference

Repository family: `Kotlin/kotlin-agent-skills`.

If available and directly relevant, treat these as high-authority Kotlin platform/tooling
specialists:

- `kotlin-tooling-java-to-kotlin` — staged Java→Kotlin conversion with framework detection and
  semantic verification;
- `kotlin-backend-jpa-entity-mapping` — Kotlin-specific JPA/Hibernate identity, equality, fetch,
  relationship and persistence pitfalls;
- `kotlin-tooling-agp9-migration` — KMP/Android Gradle Plugin migration;
- `kotlin-tooling-native-build-performance` — measured Kotlin/Native/iOS build performance;
- `kotlin-tooling-cocoapods-spm-migration` — native dependency-manager migration when applicable;
- `kotlin-tooling-immutable-collections-0-5-x-migration` — exact library migration when that
  dependency/version family is proven.

These skills are narrow by design. Load only the one matching the task.

## Java/JVM — specialized community candidates

Repository family: `decebals/claude-code-java`.

Useful installed candidates include:

- `java-code-review` — JVM-specific correctness/resource/API review;
- `concurrency-review` — Java thread-safety, executors, futures, proxy-based async, modern JVM
  concurrency;
- `jpa-patterns` — JPA/Hibernate query/fetch/transaction/locking review;
- `performance-smell-detection` — performance leads with an explicit measure-first philosophy;
- `java-migration` — major-JDK/framework migration workflow;
- `api-contract-review` and `architecture-review` — when the Java project exposes broader
  service/architecture contracts;
- `maven-dependency-audit` — Maven-specific dependency work when Maven is proven.

Version-sensitive details from community skills must be checked against the project's actual JDK,
framework versions, and current primary docs before code is changed.

## Design / visual craft — community candidates

Repository family: `Leonxlnx/taste-skill`.

Strong candidates when installed:

- `design-taste-frontend` — brief inference, anti-template design direction, adaptive visual
  variance/motion/density and design-system choice;
- `redesign-existing-projects` — audit-first redesign while preserving the existing stack;
- `image-to-code` — reference-image-first frontend production when visual fidelity is the central
  goal and image generation is available;
- `brandkit` — brand identity/art-direction systems;
- `imagegen-frontend-web` / `imagegen-frontend-mobile` — generated visual reference work for web
  or mobile when appropriate.

Design-reference atlas: `VoltAgent/awesome-design-md`.

This is not a skill bundle to install. It is a curated collection of real-product `DESIGN.md`
analyses that can improve design reasoning for image generation, branding, and frontend art
direction. When the task is visually consequential and the user/project has not already locked the
direction, use one well-matched entry (at most one secondary entry) to extract a compact reference
capsule: atmosphere, hierarchy, palette roles, typography character, composition, material/depth,
imagery treatment, responsive behavior where relevant, and a few do/don't guardrails.

The canonical Thalarch handling rules live in
`skills/thalarch-design-system/references/awesome-design-md.md`. User/project references outrank this
atlas. Do not bulk-mix brands, copy logos/proprietary identity, or claim a DESIGN.md was read unless
it was actually retrieved.

Do not apply marketing/landing-page aesthetics to dashboards, regulated/public-sector products,
or dense product UI unless the brief supports it. Accessibility, existing brand, and repository
constraints outrank aesthetic novelty.

## Broad engineering bundle — community candidates

Repository family: `alirezarezvani/claude-skills`.

Potentially high-value installed specialists include:

- `engineering-skills` — discovery/index skill; use it to locate one specific specialist, never
  bulk-load the whole bundle;
- `tdd-guide` — red/green/refactor, coverage-gap analysis, property/mutation testing ideas;
- `senior-architect` — architecture/dependency/decision workflows;
- `code-reviewer` — language-dispatched review and deterministic analyzer patterns;
- `focused-fix` — feature-level scope→trace→diagnose→fix→verify repair;
- `playwright-pro` — browser/E2E work when available and compatible;
- `senior-security` / security specialists — only for actual security scope;
- `adversarial-reviewer` — use perspective-shift techniques, but **do not inherit any rule that
  forces a finding**. Thalarch requires evidence and permits a clean review.

## Selection rule

Recognizing a trusted source is only a tie-breaker. The final ranking remains:

1. explicit user/repository contract;
2. actual task fit;
3. project-local specificity;
4. official/current platform authority;
5. version compatibility;
6. evidence/tool leverage;
7. context cost and redundancy.

If a known external skill conflicts with the repository or a current official API, discard or
narrow the skill rather than forcing the project to match the skill.
