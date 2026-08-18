---
name: thalarch-router
description: >
  Chooses the smallest compatible set of process and domain skills for a software task.
  Use before complex work, when multiple skills could apply, when skill overlap may cause
  ceremony or conflicting instructions, or when the agent needs to decide between debug,
  feature, UI, Android, security, CI, Git, architecture, and review workflows.
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
- cross-module architectural interfaces.

## Output

Return a compact routing decision:

`Mode: <...>`
`Risk: <...>`
`Skills: <ordered list>`
`Evidence required: <...>`
`Why not other skills: <only meaningful exclusions>`
