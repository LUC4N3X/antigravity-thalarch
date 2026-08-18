# Thalarch 2.1 — Design Notes

## Goal

Thalarch is designed as a project-agnostic engineering and creative-production
harness for Google Antigravity. The core must not assume a particular language,
framework, product, repository layout, operating system, or user.

Domain knowledge is layered through focused skills and loaded only when relevant.

## Progressive disclosure

Version 1 concentrated most behavior in one high-rigor skill. Version 2 introduced
a router plus focused process/domain skills. Version 2.1 extends the same model to
web and image work rather than stuffing visual rules into the core.

This is both a quality and context-efficiency decision: unused expertise should
not compete with the current problem for attention.

## Structural enforcement

The primary orchestrator intentionally has no project write tools, no shell tool,
and no direct image-generation tool.

- planners/researchers/debuggers establish evidence;
- implementers mutate engineering code;
- the web designer owns bounded frontend implementation;
- the visual director owns bounded image generation/editing;
- design/vision/code reviewers inspect independently;
- the verifier judges acceptance from a cold context.

The separation is more important than role names. It prevents the coordinator
from creating an artifact and approving the same artifact from the same context.

## Creative engineering

Visual quality is treated as a first-class deliverable rather than decoration.

For websites Thalarch separates:

1. product/audience grounding;
2. aesthetic direction;
3. semantic design system;
4. imagery strategy;
5. implementation in the existing stack;
6. real browser evidence;
7. independent design review.

For images it separates:

1. task type (inspect/generate/edit/vector/capture/compare/annotate/optimize);
2. reference-image roles;
3. visual acceptance contract;
4. production;
5. final-pixel inspection;
6. metadata/before-after checks when relevant;
7. independent vision review.

A generated website mockup is not implementation evidence. A generation prompt is
not proof of the final pixels. Source code is not proof of rendered visual quality.

## Design-system discipline

Multi-page or brand-sensitive work should have one semantic source of truth for:

- atmosphere and product character;
- color roles;
- typography architecture;
- spacing and geometry;
- component hierarchy/states;
- responsive layout;
- motion;
- imagery;
- accessibility constraints;
- project-specific anti-patterns.

The design system is extracted from existing code/assets before a redesign invents
new rules. New visual systems must be product-specific enough that the result does
not become a generic template with a swapped logo.

## Raster vs deterministic visual production

Thalarch deliberately does not use generative raster imagery for every visual job.

Use generation for semantic raster artwork and edits. Prefer deterministic SVG or
code-native production for exact logos, icons, diagrams, charts, geometry, and
mission-critical typography when that yields stronger guarantees.

This makes `generate_image` a powerful specialist tool rather than an all-purpose
hammer.

## Risk-sized review council

Review depth is proportional to risk:

- **lite** — general reviewer for a small bounded diff;
- **standard** — spec/correctness plus ordinary engineering quality;
- **visual** — design/vision review when pixels are part of acceptance;
- **deep** — independent security, performance/concurrency, and domain lenses as relevant.

More reviewers are not inherently better. Irrelevant review lenses create noise
and false positives.

## Causal debugging

Unexpected behavior is treated as an investigation problem before it is treated
as an editing problem. A root-cause hypothesis should make a prediction and name
what would disprove it.

After repeated disproven hypotheses, the protocol reassesses assumptions and
architecture rather than accumulating patches.

## Evidence hierarchy

Thalarch separates claims by what the evidence can actually prove:

- lint does not prove compilation;
- compilation does not prove runtime behavior;
- unit tests do not prove cross-service integration;
- generated mockups do not prove implementation;
- prompts do not prove image fidelity;
- standalone asset QA does not prove responsive page integration;
- screenshots prove a visual state, not an entire interaction flow;
- an implementer/creator report does not prove acceptance.

`PASS`, `FAIL`, and `UNVERIFIED` remain intentionally distinct.

## Knowledge compounding

Difficult tasks may yield reusable lessons, but Thalarch keeps them ephemeral by
default. A lesson becomes durable repository documentation only when the user or
project explicitly chooses a knowledge sink.

This prevents permanent rule files from filling with task-specific noise.

## External actions

The protocol distinguishes local implementation from consequential external side
effects. Commit/push/PR, merge, publish/release, deployment, permission changes,
and destructive operations are separate authorization classes.

An optional command hook can harden this boundary, but it is disabled by default
because hooks can affect every session using the plugin.

## Self-evaluation

Thalarch ships representative eval prompts because prompt size and agent count are
poor proxies for quality.

Changes should be measured against:

- routing accuracy;
- unnecessary ceremony;
- scope discipline;
- root-cause-before-fix compliance;
- acceptance coverage;
- review false-positive rate;
- verification honesty;
- external-action discipline;
- context/turn cost;
- cross-project portability;
- website distinctiveness without usability loss;
- responsive/browser proof;
- image reference-role correctness;
- collateral-drift resistance in image edits;
- visual-review honesty.

A longer prompt that does not improve behavior is a regression.
