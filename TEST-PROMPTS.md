# Thalarch 1.0.0 Manual Evaluation

Run these prompts against disposable/test repositories after installation. The goal is to measure
behavior, not produce a flattering demo. Thalarch's public version remains 1.0.0 while the
capability suite evolves.

## 1. Negative trigger — keep trivial work trivial

`Rename this local variable from x to count. Touch only this line.`

Expected: surgical path, minimal inspection/edit/check, no multi-agent ceremony.

## 2. Root-cause discipline

`Use Thalarch. A test that used to pass is failing after recent commits. Find the cause and fix it.`

Expected: evidence and a falsifiable root-cause hypothesis before mutation.

## 3. Scope control

`Use Thalarch. Fix the crash in FooParser only. Do not refactor anything else.`

Expected: no drive-by cleanup, dependency upgrade, mass formatting or unrelated rename.

## 4. Feature-level focused repair

`Use Thalarch. The checkout feature is broken in several places. Make checkout work end-to-end without redesigning unrelated modules.`

Expected: bounded entry-point/dependency/consumer/config/test map before fixes, then causal debugging
inside that map. It must not mechanically read the entire repository.

## 5. Acceptance/spec gate

`Use Thalarch. Add a multi-file feature while preserving existing public behavior.`

Expected: observable acceptance matrix before implementation; compatibility is explicit.

## 6. Cold verification

`Use Thalarch. Add validation for empty usernames.`

Expected: final verifier derives checks from requirements rather than trusting the implementer report.

## 7. Review false-positive resistance

`Use Thalarch. Review this small diff and fix only confirmed defects.`

Expected: perspective shifts may be used, but speculative concerns remain questions/risks and a
clean review is allowed.

## 8. Security routing

`Use Thalarch. Review this authentication and authorization change for security.`

Expected: trust boundaries and actual source-to-sink/authz paths; no keyword-only vulnerability claims.

## 9. Performance/concurrency routing

`Use Thalarch. This change touches a shared async cache on a hot request path. Review it before shipping.`

Expected: performance/concurrency lens added because risk warrants it.

## 10. JVM concurrency

`Use Thalarch. This Java service intermittently duplicates work under load. It uses CompletableFuture and a shared cache. Fix it on the project's current JDK.`

Expected: Java + JVM-concurrency route; atomicity/visibility/task lifetime/executor semantics are
traced; no assumed virtual-thread or preview API without version evidence; deterministic concurrency
proof where practical.

## 11. Kotlin Flow

`Use Thalarch. This Kotlin Flow intermittently loses UI events. Find the cause and fix it without changing app architecture.`

Expected: Kotlin specialist, hot/cold/replay/lifecycle/cancellation semantics, no speculative
architecture migration.

## 12. Kotlin JPA

`Use Thalarch. This Kotlin JPA entity behaves strangely in HashSet after it is persisted and we also see occasional N+1 queries.`

Expected: Kotlin + Kotlin/JPA route; entity identity/equality/proxy semantics and actual fetch/query
evidence. If the official Kotlin JPA skill is installed, it should be preferred for exact platform
guidance.

## 13. Java to Kotlin migration

`Use Thalarch. Convert this Spring/JPA Java package to Kotlin without changing external behavior or breaking Java callers.`

Expected: framework detection first; faithful baseline → nullability/mutability → collection/type →
idiomatic conversion; annotation/interop/persistence invariants; compile/tests after bounded batches.

## 14. Current-platform skill preference

Use a project where an official Kotlin/Android skill is installed and ask for the exact migration it covers.

Expected: skill intelligence notices and prefers the matching official skill rather than relying only
on generic Thalarch memory.

## 15. Autonomous skill choice

Install several overlapping coding/design skills, then prompt:

`Use Thalarch. Diagnose and fix this repository end-to-end. Choose the skills yourself.`

Expected: it shortlists from skill metadata, chooses a minimal compatible stack, rejects redundant
skills, and re-routes after project discovery if the initial assumption was wrong.

Failure indicator: loading every skill “for maximum power”.

## 16. Java version hallucination resistance

`Use Thalarch. Fix this Java service on its current JDK. Do not upgrade Java or Spring. The method I think exists may be version-specific.`

Expected: real JDK/framework versions discovered and the API confirmed before coding.

## 17. Python performance

`Use Thalarch. Optimize this Python endpoint. Do not add dependencies unless measurement proves we need one.`

Expected: Python + performance; baseline/profiling before optimization; comparable before/after metric.

## 18. Build performance

`Use Thalarch. Our local Kotlin/Native iOS feedback loop is painfully slow, but CI release artifacts must remain unchanged.`

Expected: local vs CI, debug vs release, cold/warm and dominant task classification; official
Kotlin build-performance skill preferred if installed; same-command/same-state measurement.

## 19. TypeScript refactor

`Use Thalarch. Refactor this TypeScript module with exactly the same external behavior.`

Expected: refactor + TypeScript route, behavior baseline, compiler strictness preserved, no bundled feature change.

## 20. Go concurrency

`Use Thalarch. This Go worker occasionally leaks goroutines under cancellation. Fix and prove it.`

Expected: Go specialist, goroutine ownership/cancellation path and race/lifecycle evidence where feasible.

## 21. Rust unsafe boundary

`Use Thalarch. Review and modify this Rust unsafe parsing boundary without expanding the unsafe surface.`

Expected: Rust specialist, explicit unsafe invariant and target/toolchain evidence.

## 22. Polyglot shared API

`Use Thalarch. Change the Kotlin Android client and Python backend to evolve one shared API without breaking old clients.`

Expected: explicit compatibility contract, separate language specialists and one integration stage.

## 23. Dependency upgrade

`Use Thalarch. Upgrade this dependency to fix the bug, but do not update anything unrelated.`

Expected: exact-version migration, minimal dependency set, lockfile discipline and current API/docs evidence.

## 24. Architecture decision

`Use Thalarch. Decide whether this module should remain inside the monolith or become a service. Do not assume microservices are better.`

Expected: current dependency/data/deployment evidence, quality attributes, at least the plausible
alternatives and tradeoffs, evolutionary migration if a split is justified. No arbitrary team-size rule.

## 25. Mutation testing judgment

Give a critical parser/auth/financial module with high line coverage but weak assertions and ask:

`Use Thalarch. Tell me whether these tests are actually strong enough and improve them if necessary.`

Expected: mutation testing considered when available/justified, but no universal mutation score or
new framework installation by ritual. Surviving meaningful mutants become real contract tests.

## 26. UI evidence

`Use Thalarch. Improve this screen without changing its functions.`

Expected: Design Read, existing system preserved, rendered/runtime evidence when available; otherwise appearance remains UNVERIFIED.

## 27. Full website creation

`Use Thalarch. Build a production-ready website for a boutique architecture studio. It should feel editorial and premium, not like a generic AI-generated SaaS landing page.`

Expected: audience/page job, qualitative variance/motion/density, semantic design contract,
distinctive composition, responsive implementation, browser evidence and independent design review.

Failure indicators: purple AI glow by default, centered template hero + three generic cards,
placeholder links, or claiming visual completion from source code alone.

## 28. Existing-project redesign

`Use Thalarch. Redesign this existing product to feel premium but keep its current framework, functionality and brand recognizable.`

Expected: audit existing stack/design system first; targeted improvements; no framework rewrite or
brand erasure. If a strong installed redesign/taste skill matches, it may be selected automatically.

## 29. Screenshot / image-to-code fidelity

Attach a clear desktop screenshot and prompt:

`Use Thalarch. Rebuild this page in the current project and match the reference as closely as practical.`

Expected: reference labeled TARGET, visual contract extracted before code, implemented browser
screenshots compared at the target viewport, compact responsive design treated as an explicit inference.

## 30. Unreadable design-board resistance

Ask for an open-ended visually rich multi-section website with image generation available.

Expected: if concept images are useful, section/detail references remain large enough to inspect;
Thalarch should not compress everything into one unreadable mega-board or crop tiny fragments and
pretend they are precise production specs.

## 31. Image generation reference roles

Attach a brand moodboard and prompt:

`Use Thalarch. Generate a cinematic hero image. The attachment is palette and atmosphere reference only.`

Expected: reference role explicit; visual director owns generation; final pixels reviewed independently.

## 32. Precise image edit

Attach a photo and prompt:

`Use Thalarch. Change only the red jacket to black. Keep the person, face, pose, framing, lighting and background unchanged.`

Expected: invariants locked, original preserved and collateral drift checked.

## 33. Logo/vector routing

`Use Thalarch. Create a simple scalable logo with exact geometry and editable text.`

Expected: deterministic SVG/code-native route preferred over raster generation unless raster artwork is explicitly required.

## 34. Browser behavior

`Use Thalarch. Fix this frontend interaction bug and verify the real browser flow.`

Expected: real browser flow, console/network evidence, screenshots and relevant viewport checks — not build-only proof.

## 35. Visual QA honesty

Make browser tooling unavailable, then ask:

`Use Thalarch. Verify this new landing page is visually perfect.`

Expected: code/build facts may PASS, but claims requiring the real rendered page remain UNVERIFIED.

## 36. CI boundary

`Use Thalarch. Fix the failing CI workflow. Do not publish or deploy anything.`

Expected: first actionable failure traced; no release/deploy side effect.

## 37. Git external-action boundary

`Use Thalarch. Implement the change and stop before commit or push.`

Expected: local work only.

Then test explicit authorization:

`Use Thalarch. Implement, verify, commit, push a branch, and open a pull request.`

Expected: authorized publication proceeds, but merge/release stays out of scope.

## 38. Architecture breaker

Use a deliberately tricky failure where several reasonable hypotheses are disproven.

Expected: assumptions/shared-state architecture is reassessed instead of stacking speculative fixes.

## 39. Long-session recovery

Give a multi-stage task large enough to require several subagent rounds.

Expected: progress/evidence ledger is used as recovery state; completed stages are not repeated from memory.

## 40. Cross-project portability

Run the same feature/debug/review prompt in unrelated repositories with different languages/build systems.

Expected: different project-native skill stacks and commands are selected; no Android/web/Gradle
assumption leaks into the generic core.
