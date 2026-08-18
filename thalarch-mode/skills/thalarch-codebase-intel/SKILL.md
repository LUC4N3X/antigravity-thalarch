---
name: thalarch-codebase-intel
description: >
  Builds a bounded, evidence-backed mental model of an unfamiliar or large repository
  before architecture work, broad refactors, onboarding, or cross-module debugging. Use when
  the relevant control flow is not yet known; avoid for narrow routine edits.
---

# Thalarch Codebase Intel

Do not "read the repo". Build only the map needed for the task.

## Scan order

1. repository rules and intent docs;
2. build manifests and module graph;
3. entry points relevant to the task;
4. data/control flow;
5. tests around the same behavior;
6. CI/runtime integration points;
7. recent Git history for the affected surface.

Every architectural claim needs a concrete file path, command output, or source location.

Mark:
- `FACT`
- `INFERENCE`
- `UNKNOWN`

Do not silently turn inference into fact.

## Deliverable

Create a task-focused context packet:
- stack/modules;
- relevant call/data-flow;
- important interfaces/invariants;
- existing patterns to reuse;
- tests/build commands;
- risk hotspots;
- open unknowns.

Do not create permanent documentation unless requested.

## Optional project probe

When shell execution is available, `scripts/project_probe.py` provides a read-only
snapshot of repository rules, build markers, Git branch/status, changed files, and
recent commits. Run it as a black box before reading its source:

`python scripts/project_probe.py --path <workspace>`

The probe is orientation evidence, not a substitute for reading task-relevant code.
