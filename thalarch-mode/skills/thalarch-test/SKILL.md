---
name: thalarch-test
description: >
  Designs high-value regression, property, integration, and fuzz-style tests for behavior
  changes. Use after a root cause is known or a feature contract exists. Focuses on tests that
  can actually falsify the implementation, negative/error paths, red-green proof, boundary
  matrices, and avoiding mock-heavy tests that merely restate implementation details.
---

# Thalarch Test

Testing exists to falsify the implementation, not to decorate the diff.

## Test selection

Prefer the cheapest layer that proves the contract:

1. pure/unit;
2. property/state-machine/model test;
3. component/module;
4. integration with the real boundary;
5. device/browser/end-to-end.

Move upward only when the lower layer cannot prove the behavior. Do not substitute a lower layer
for an acceptance criterion that fundamentally lives higher in the stack.

## Quality rules

A useful test:

- asserts user- or contract-visible behavior;
- fails for a meaningful broken implementation;
- controls unrelated nondeterminism;
- covers the actual regression mechanism or invariant;
- has a clear reason for its layer;
- does not merely mirror private implementation details;
- does not pass only because a mock returns the expected answer.

For bug fixes, prefer red-green proof:

1. reproduce the original failure;
2. prove the test/check fails for the broken behavior when practical;
3. apply the fix;
4. rerun the same proof;
5. run nearby regressions.

## Boundary matrix

For parsers, indexing, pagination, ranges, state transitions, concurrency, validation, or data
conversion, enumerate meaningful cases before implementation/testing:

- empty / one / many;
- minimum / maximum / just outside boundaries;
- null/absent/optional states where the contract permits them;
- duplicate/reordered input;
- Unicode/encoding/byte boundaries where relevant;
- timeout/cancellation/retry;
- repeated/idempotent operations;
- concurrent interleavings when state is shared.

Do not manufacture irrelevant cases just to increase test count.

## Property and metamorphic testing

When behavior has strong invariants and the repository already has or justifiably needs the
required tooling, prefer properties over a long list of hand-picked examples.

Examples:

- encode/decode round trip;
- parse/serialize stability;
- sorting preserves elements and order invariant;
- normalization is idempotent;
- cache result equals uncached result;
- optimized implementation agrees with a simple reference model;
- adding irrelevant input does not alter an independent output.

Use the language ecosystem already present: Hypothesis, jqwik/QuickTheories, Kotest property,
Go fuzzing, proptest/quickcheck, fast-check, or equivalent only when compatible with the project.

## Fuzzing

Fuzz parsers, codecs, protocol/state-machine boundaries, file formats, untrusted input handlers,
and serialization when malformed or adversarial input is a real risk.

A discovered fuzz failure becomes a small deterministic regression case before completion.

Do not run security-oriented network fuzzing against systems without authorization.

## Concurrency tests

Avoid real sleeps as synchronization when controllable schedulers, latches, barriers, virtual
time, deterministic dispatchers, or test hooks can prove the ordering more reliably.

A flaky test is not acceptable evidence. Diagnose the race or make the synchronization explicit.

## Mutation strength

Ask: “What realistic broken implementation would still pass this test?” If the answer is easy to
name, strengthen the assertion or choose a better layer.

## Report

For every material test/check state:

- what contract it proves;
- which failure/regression it would catch;
- what it does not prove;
- whether it ran successfully in the current environment.
