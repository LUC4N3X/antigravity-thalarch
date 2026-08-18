---
name: thalarch-review
description: >
  Runs risk-sized, evidence-first review of code changes. Use before completion, PR creation,
  or after meaningful implementation. Separates requirement compliance from engineering quality,
  uses independent reviewer contexts, confirms findings before fixing them, and supports lite,
  standard, and deep review depth.
---

# Thalarch Review

## Review Council

## Lens 1 — Spec compliance

For every acceptance item:
- PASS;
- FAIL;
- UNVERIFIED;
- OUT OF SCOPE.

Check for unrequested change.

## Lens 2 — Correctness/regression

Inspect:
- lifecycle/state ownership;
- boundaries and edge cases;
- async/concurrency;
- resource cleanup;
- persistence/migrations;
- network cancellation/retry;
- compatibility;
- test validity.

## Lens 3 — Security (when relevant)

Use `thalarch-security`.

## Lens 4 — Performance (when relevant)

Ask:
- does the diff add repeated work to a hot path?
- unbounded memory/state?
- blocking I/O?
- unnecessary recomposition/rendering?
- N+1/network fan-out?
- contention/race risks?

## Finding contract

A confirmed finding must have:
- severity;
- path/location;
- concrete failure mode;
- evidence/counterexample;
- minimal remediation.

Low-confidence speculation is a question, not a defect.

## Fix loop

Batch compatible confirmed findings.
Re-run checks invalidated by the fix.
Do not restart a full review unless the fix materially expands the changed surface.
