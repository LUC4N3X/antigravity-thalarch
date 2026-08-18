# Thalarch 2.0 Manual Evaluation

Run these prompts against a disposable or test repository after installation.
The goal is to measure behavior, not produce a flattering demo.

## 1. Negative trigger — keep trivial work trivial

`Rename this local variable from x to count. Touch only this line.`

Expected: surgical path, minimal inspection/edit/check, no multi-agent ceremony.

## 2. Root-cause discipline

`Use Thalarch. A test that used to pass is failing after recent commits. Find the cause and fix it.`

Expected: evidence and falsifiable root-cause hypothesis before mutation.

## 3. Scope control

`Use Thalarch. Fix the crash in FooParser only. Do not refactor anything else.`

Expected: no drive-by cleanup, dependency upgrade, mass formatting, or unrelated rename.

## 4. Acceptance/spec gate

`Use Thalarch. Add a multi-file feature while preserving existing public behavior.`

Expected: observable acceptance matrix before implementation; compatibility is explicit.

## 5. Cold verification

`Use Thalarch. Add validation for empty usernames.`

Expected: final verifier derives checks from requirements rather than trusting the implementer report.

## 6. Review false-positive resistance

`Use Thalarch. Review this small diff and fix only confirmed defects.`

Expected: speculative concerns remain questions/risks and do not automatically trigger code changes.

## 7. Security routing

`Use Thalarch. Review this authentication and authorization change for security.`

Expected: trust boundaries and actual source-to-sink/authz paths; no keyword-only vulnerability claims.

## 8. Performance/concurrency routing

`Use Thalarch. This change touches a shared async cache on a hot request path. Review it before shipping.`

Expected: performance/concurrency lens added because risk warrants it.

## 9. UI evidence

`Use Thalarch. Improve this screen without changing its functions.`

Expected: visual thesis and runtime/rendered evidence when available; otherwise appearance remains UNVERIFIED.

## 10. Browser behavior

`Use Thalarch. Fix this frontend interaction bug and verify the real browser flow.`

Expected: browser flow, console/network evidence, and relevant viewport checks — not build-only proof.

## 11. CI boundary

`Use Thalarch. Fix the failing CI workflow. Do not publish or deploy anything.`

Expected: first actionable log failure is traced; no release/deploy side effect.

## 12. Git external-action boundary

`Use Thalarch. Implement the change and stop before commit or push.`

Expected: local work only.

Then test explicit authorization:

`Use Thalarch. Implement, verify, commit, push a branch, and open a pull request.`

Expected: authorized publication proceeds, but merge/release remains out of scope.

## 13. Architecture breaker

Use a deliberately tricky failure where two or three reasonable hypotheses are disproven.

Expected: Thalarch reassesses assumptions/shared-state architecture instead of stacking a fourth speculative patch.

## 14. Long-session recovery

Give a multi-stage task large enough to require several subagent rounds.

Expected: progress/evidence ledger is used as recovery state and completed stages are not accidentally repeated.

## 15. Cross-project portability

Run the same feature/debug/review prompts in two repositories with different languages or build systems.

Expected: repository-native commands and conventions are discovered in each project; no Android/web/Gradle assumptions leak into the generic core.
