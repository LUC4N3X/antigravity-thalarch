---
name: thalarch-router
description: >
  Chooses the smallest compatible set of process and domain skills for a software task.
  Use before complex work, when multiple skills could apply, when skill overlap may cause
  ceremony or conflicting instructions, or when the agent needs to decide between debug,
  feature, UI, image/visual, Android, security, CI, Git, architecture, and review workflows.
---

# Thalarch Router

Classify before loading heavy instructions.

## Decision

1. Identify the task's primary failure/goal type.
2. Estimate risk: low / medium / high.
3. Identify evidence needed for completion.
4. Select the smallest skill stack that covers the task.
5. Prefer process skills before domain skills.
6. Prefer official current platform skills when installed.
7. Do not load unrelated skills "just in case".
8. If an image is an input/output/reference, decide whether the task is inspect,
   generate, edit, vector, capture, compare, annotate, or optimize before routing.

## Risk signals

Raise risk when the change involves:
- auth/security/privacy;
- concurrency or shared state;
- persistence or migration;
- networking/protocol parsing;
- build/release/signing;
- broad refactor;
- user data;
- runtime behavior hard to reproduce;
- cross-module architectural interfaces;
- exact visual identity/brand preservation;
- image edits where "change only X" must preserve locked regions;
- production assets with exact text, transparency, dimensions, or export constraints.

## Image routing

Use these stacks when visual artifacts are central:

- new raster image → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- precise image edit → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- inspect/compare image → `thalarch-image` + `thalarch-visual-qa`;
- logo/icon/diagram requiring exact vector geometry → `thalarch-image` +
  deterministic vector/code path + `thalarch-visual-qa`;
- web UI screenshot evidence → `thalarch-ui` + `thalarch-browser-qa` +
  `thalarch-visual-qa`;
- UI that needs generated artwork → `thalarch-ui` + `thalarch-imagegen` +
  runtime QA + `thalarch-visual-qa`.

## Output

Return a compact routing decision:

`Mode: <...>`
`Risk: <...>`
`Skills: <ordered list>`
`Evidence required: <...>`
`Why not other skills: <only meaningful exclusions>`
