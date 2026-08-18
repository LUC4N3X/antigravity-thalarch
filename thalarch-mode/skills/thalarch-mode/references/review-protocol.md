# Review Protocol

Review is evidence gathering, not bug invention.

## Pass 1 — Requirement compliance

Build a checklist directly from the user's request.

For each item mark:

- PASS — directly supported by code/evidence;
- FAIL — confirmed mismatch;
- UNVERIFIED — cannot be proven with available evidence;
- OUT OF SCOPE — not requested.

Also inspect the diff for work the user did not request.

## Pass 2 — Correctness and regressions

Inspect:

- state transitions and lifecycle;
- null/empty/error paths;
- boundary values;
- async/concurrency races;
- resource cleanup;
- persistence/migrations;
- network retry/cancellation;
- backward compatibility;
- performance hot paths;
- security/privacy;
- API contracts and parsing assumptions.

## Pass 3 — Test quality

Tests must prove behavior, not merely execute code.

Reject as insufficient:

- tests with no meaningful assertion;
- mocks that bypass the logic under test;
- tests that only restate implementation details;
- a test that passes both before and after the intended fix.

## Finding standard

Every reported issue should contain:

1. severity;
2. exact file/location;
3. concrete failure mode;
4. evidence or reproducer;
5. minimal recommended correction.

If you cannot produce evidence or a credible counterexample, label the item as a
question/risk rather than a confirmed defect.

## Review independence

A cold reviewer should receive the requirement and diff, not the implementer's
reasoning narrative. This reduces inherited blind spots and confirmation bias.
