# Thalarch 1.0.0 — Design Notes

## Permanent version policy

Thalarch's public version remains **1.0.0**. New capabilities are treated as continuous evolution
of the same protocol and are recorded in Git history and `CHANGELOG.md`, not as public version
bumps.

## Goal

Thalarch is a project-agnostic, **model-agnostic** engineering and creative-production reliability
harness. The core must not assume a particular host agent, language, framework, product, repository
layout, operating system, user, or preferred aesthetic.

Expertise is progressively disclosed through focused skills and loaded only when evidence says it
is relevant.

## One core, thin host adapters

The canonical engineering doctrine lives in `thalarch-mode/skills/`. Host support must not fork
those skills into separately evolving copies.

Adapters translate only what genuinely differs between hosts:

- skill discovery/install locations;
- persistent instruction files;
- custom-agent/subagent formats;
- lifecycle-hook event/wire formats;
- host-specific tool names and capabilities.

Google Antigravity remains the richest native orchestration implementation. Codex maps the same
reliability contract onto Agent Skills, `AGENTS.md`, native hooks, and its own agent/worktree
facilities. Claude Code maps it onto skills, `CLAUDE.md`, custom subagents, and Claude-native hooks.

If a host lacks a capability, Thalarch must report the affected claim `UNVERIFIED` or choose a
supported fallback rather than pretend the Antigravity capability exists everywhere.

## Skill intelligence

Thalarch does not hard-code one giant expert prompt.

The active coordinator first inspects available skill metadata, then combines:

- explicit user/repository constraints;
- project-local skills;
- current official/vendor skills;
- Thalarch process/language/domain skills;
- trusted third-party specialists when they add unique value.

It can re-route after repository discovery and can remove skills that became irrelevant.

The design goal is **best-fit minimal expertise**, not maximum skill count.

## Progressive disclosure

Unused expertise should not compete with the current problem for context.

A Kotlin/JPA task may need Kotlin + an official JPA specialist + data verification. A tiny Python
rename should not load Android, security, design, architecture and six reviewers.

This is both a quality and context-efficiency decision.

## Structural enforcement

On Antigravity, the primary orchestrator intentionally has no project write tools, shell tool, or
direct image-generation tool.

Across hosts the architectural intent remains the same even when the host's primitives differ:

- planners/researchers/debuggers establish evidence;
- language/implementation specialists mutate code;
- web/visual specialists own bounded creative production where tools exist;
- code/design/vision reviewers inspect independently;
- fact checking verifies exact material claims;
- the verifier judges acceptance from a cold context.

The separation prevents one context from creating an artifact and then treating its own narrative
as proof of quality.

## Epistemic reliability

Thalarch treats factual reliability as a first-class engineering property.

Material claims are classified by the evidence they require: repository, external/version-sensitive,
runtime, visual, or derived inference. Cheaply inspectable facts should be inspected before they are
asserted. Missing evidence is represented explicitly as `UNKNOWN` or `UNVERIFIED` rather than filled
with a plausible invention.

Host-native hooks enforce only failure modes that can be checked deterministically enough to justify
a hard gate. Hooks do not attempt to prove arbitrary semantic correctness with regexes.

A verification result is fresh only when it is newer than the final relevant mutation. Earlier
passing tests cannot be reused as evidence for code changed afterward.

## Adaptive reasoning

Reasoning depth is proportional to uncertainty and consequence rather than always maximal.

- D0/D1 keep routine work fast;
- D2 introduces explicit fact/inference/unknown separation and disconfirmation;
- D3 adds independent challenge/adjudication for difficult architecture/debug/security/concurrency;
- D4 adds stronger independence, negative testing, invariants and recovery thinking for critical
  work.

The visible artifact is compact evidence and decisions, not private chain-of-thought.

## Polyglot engineering

Language expertise is project-version-aware.

The dedicated Java, Kotlin, Python, TypeScript/JavaScript, Go and Rust specialists first discover
the project's real compiler/runtime, package/build tooling, framework/dependency versions and test
conventions.

Version-sensitive APIs must be confirmed from repository/resolved dependency evidence or current
primary documentation instead of generated from memory.

Official platform skills can outrank Thalarch's generic language guidance when they match the exact
proven task. This is especially important for Kotlin/JetBrains and Android tooling that evolves
quickly.

## JVM and Kotlin specialization

Shared JVM concerns are separated from generic Java/Kotlin style:

- concurrency correctness has explicit atomicity, visibility, task-lifetime, cancellation and
  version-aware virtual-thread/async review;
- Kotlin migrations preserve behavior/API/nullability/framework/data invariants before idiomatic
  transformation;
- Kotlin JPA work treats identity, equality, generated IDs, proxying, lazy fetch, transactions and
  uniqueness as one persistence contract.

Narrow official/installable specialists remain preferable for exact current platform migration
facts.

## Architecture

Architecture decisions begin with the current system and its quality attributes.

Thalarch compares plausible alternatives, including the simplest one, and records tradeoffs rather
than using fixed rules such as “team size X means microservices”.

Architecture changes should be evolutionary and reversible where possible, with explicit data,
contract, deployment and rollback consequences.

## Causal debugging and focused repair

Unexpected behavior is investigated before it is edited.

For isolated failures, a root-cause hypothesis must make a prediction and name what would disprove
it. For a broken feature/module, Thalarch first maps the bounded entry points, dependencies,
consumers, configuration and related tests, then investigates individual causal failures.

After repeated disproven fix hypotheses or cascading fixes, assumptions/shared-state architecture
are reassessed instead of accumulating patches.

## Testing philosophy

Tests are evidence, not a score.

Thalarch can use:

- unit/component/integration/device/browser tests;
- property/metamorphic tests;
- fuzzing;
- deterministic concurrency tests;
- risk-based mutation testing.

Coverage and mutation percentages are not universal quality thresholds. A test is valuable when it
would fail for a meaningful broken implementation of a real contract.

## Performance

Runtime and build performance require comparable before/after evidence.

Build investigations distinguish local/CI, debug/release, cold/warm/incremental/no-op state and the
actual phase dominating the command the user waits for. Optimizing the local loop must not silently
remove required CI/release behavior.

Unmeasured performance conclusions remain `UNVERIFIED`.

## Creative engineering

Visual quality is a first-class deliverable.

For websites Thalarch separates:

1. brief/audience/trust inference (`Design Read`);
2. aesthetic variance/motion/density calibration;
3. semantic design system;
4. imagery/reference strategy;
5. implementation in the existing stack;
6. real browser evidence;
7. independent design review.

For images it separates task type, reference roles, visual acceptance contract, production, final-
pixel inspection, metadata/before-after checks and independent review.

For reference-driven frontend work, `thalarch-image-to-code` converts screenshots/mockups into an
explicit visual contract before coding and verifies the real browser result afterward.

A generated mockup is not implementation evidence. A generation prompt is not proof of final
pixels. Source code is not proof of rendered quality.

## Anti-template design discipline

Visual taste is inferred from the product rather than imposed as one house style.

Thalarch deliberately resists recurring AI defaults when they are not justified: purple glow,
centered hero + equal cards, nested shells, arbitrary pills, generic copy, ubiquitous glass and
motion everywhere.

Existing brand, accessibility, regulated/public-sector constraints and real product usability have
higher authority than novelty.

## Risk-sized review council

Review depth is proportional to changed risk:

- **lite** — independent general review for small bounded changes;
- **standard** — spec/correctness + engineering review;
- **specialized** — security, performance/concurrency, data/API, platform or visual review only
  when those surfaces exist.

Reviewers use perspective shifts to break self-review blind spots, but they are never required to
invent a defect. Findings need a concrete violated invariant/failure path and evidence.

## Deterministic helpers

Small read-only scripts are preferred over more prose when they improve orientation or evidence.
Examples include project/language probing, diff risk-lens probing and image comparison.

Their output is a lead, not a verdict. Material findings still require source/runtime confirmation.

## Evidence hierarchy

Thalarch separates claims by what evidence proves:

- lint does not prove compilation;
- compilation does not prove runtime behavior;
- line coverage does not prove assertion strength;
- unit tests do not prove external integration;
- generated mockups do not prove implemented UI;
- prompts do not prove image fidelity;
- screenshots prove a visual state, not an entire interaction flow;
- an implementer/creator report does not prove acceptance.

`PASS`, `FAIL`, and `UNVERIFIED` remain intentionally distinct.

## Knowledge compounding

Difficult tasks may yield reusable lessons, but durable repository rules are not written by default.
A lesson becomes permanent only when the project has an intentional knowledge sink or the user asks
for it.

## External actions

Commit/push/PR, merge, publish/release, deployment, permission changes and destructive operations
remain separate authorization classes.

Host-native command hooks can harden this boundary, but they must never silently broaden user
authorization or substitute a host-level permission prompt for a Thalarch completion claim.

## Self-evaluation

Thalarch measures behavior rather than prompt length or agent count.

Evaluation should cover routing accuracy, unnecessary ceremony, scope discipline, API/version
hallucination resistance, root-cause behavior, cross-language correctness, review false positives,
verification honesty, context cost, cross-project portability, **cross-model portability**, design
distinctiveness, browser/device evidence, image-reference role correctness and collateral-drift
resistance.

A longer prompt or another adapter that does not improve measurable behavior is a regression.
