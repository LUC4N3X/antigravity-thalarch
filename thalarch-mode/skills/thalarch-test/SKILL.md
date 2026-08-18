---
name: thalarch-test
description: >
  Designs high-value regression tests and verification for behavior changes. Use after a
  root cause is known or a feature contract exists. Focuses on tests that can actually fail,
  negative/error paths, red-green proof where practical, and avoiding mock-heavy tests that
  only restate the implementation.
---

# Thalarch Test

Testing exists to falsify the implementation.

## Test selection

Prefer the cheapest layer that proves the contract:
1. pure/unit;
2. component/module;
3. integration;
4. device/browser/end-to-end.

Move upward only when the lower layer cannot prove the behavior.

## Quality rules

A useful test:
- asserts user- or contract-visible behavior;
- fails for a meaningful broken implementation;
- controls unrelated nondeterminism;
- covers a boundary or regression mechanism;
- does not merely mirror private implementation details.

For bug fixes, prefer a red-green demonstration:
- reproduce failing case;
- apply fix;
- verify same case passes.

Exercise at least one error/negative path when feasible.

Mocks are not proof of cross-layer integration.

## Report

State exactly what each test proves and what it does not prove.
