---
name: thalarch-router
description: >
  Chooses the smallest compatible process, language, domain, platform, visual, and installed-skill
  stack for a task. Use before complex work and after project discovery. Combines autonomous skill
  intelligence with task, stack, risk, and evidence routing instead of requiring the user to
  manually name the best skills.
---

# Thalarch Router

Use `thalarch-skill-intelligence` before loading heavy instructions.

## Decision

1. Inspect the skill inventory exposed by the current Antigravity session.
2. Shortlist skills by description without opening every full `SKILL.md`.
3. Identify the task's primary goal/failure type.
4. Detect the actual language/runtime/toolchain/framework from repository evidence.
5. Estimate risk: low / medium / high.
6. Identify evidence needed for completion.
7. Select the smallest compatible process + language + domain + platform stack.
8. Prefer project-local and current official platform/vendor skills when they are more specific
   than a generic Thalarch or community skill.
9. Remove redundant or conflicting skills instead of stacking everything.
10. Re-run selection after preflight when new stack/version/root-cause evidence changes the route.
11. For image inputs/outputs, classify inspect/generate/edit/vector/capture/compare/annotate/optimize.

## Core process routing

- small safe edit → `thalarch-code-craft` + lightweight review;
- isolated bug/regression → `thalarch-debug` + language overlay + `thalarch-test` + review;
- broken feature/module with several dependent surfaces → bounded scope/trace/diagnose workflow
  using codebase intelligence + debug + relevant language/domain skills;
- feature → `thalarch-spec` + language overlay + `thalarch-test` + review;
- architecture/system design → `thalarch-spec` + `thalarch-codebase-intel` +
  `thalarch-architecture` + relevant language/domain + deep review;
- behavior-preserving refactor → `thalarch-refactor` + language overlay + test + review;
- performance → `thalarch-performance` + language overlay + performance review;
- API/service boundary → language overlay + `thalarch-api` + security/data skills as relevant;
- database/ORM/migration → language overlay + `thalarch-data-sql` + test/review;
- dependency/toolchain change → `thalarch-dependency` + affected language/domain + compatibility verification;
- security → `thalarch-security` + relevant language/domain + review council;
- CI → `thalarch-ci` + language/toolchain overlay + security when relevant;
- Git/publication → `thalarch-git` + review + remote-state verification.

`thalarch-code-craft` is the default universal coding overlay for meaningful mutation/review unless
a stronger project-specific coding skill already covers the same concern without losing Thalarch's
scope and verification invariants.

## Language detection and routing

Use source files plus build manifests. Do not infer from repository name alone.

- Java (`.java`, Maven/Gradle JVM Java source) → `thalarch-java` / `thalarch-java-engineer`;
- Kotlin (`.kt`, `.kts`, Kotlin Gradle plugins) → `thalarch-kotlin` / `thalarch-kotlin-engineer`;
- Python (`.py`, `pyproject.toml`, Python package metadata) → `thalarch-python` / `thalarch-python-engineer`;
- TypeScript/JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`, package scripts) → `thalarch-typescript` / `thalarch-typescript-engineer`;
- Go (`.go`, `go.mod`) → `thalarch-go` / `thalarch-go-engineer`;
- Rust (`.rs`, `Cargo.toml`) → `thalarch-rust` / `thalarch-rust-engineer`.

If an installed project-local or official language/framework skill is more specific, use it with or
instead of the generic language overlay as judged by `thalarch-skill-intelligence`.

For mixed-language changes, choose the minimum set that covers the changed boundary. Use separate
specialists for independent implementation surfaces and an explicit integration stage for the
shared contract.

If no dedicated language skill exists, use `thalarch-code-craft`, project-native conventions, and
current primary documentation for version-sensitive APIs.

## JVM specialization

Add only when evidence proves the surface:

- Java/Kotlin shared-state, threads, executors, futures, virtual threads, proxy async, locks or
  thread-safety → `thalarch-jvm-concurrency` plus the language skill;
- Kotlin + JPA/Hibernate/Spring Data entity/repository/fetch/transaction work →
  `thalarch-kotlin-jpa`, while preferring an available official Kotlin JPA skill for exact facts;
- Java → Kotlin or Kotlin/tooling conversion where semantic compatibility matters →
  `thalarch-kotlin-migration`, plus the most specific installed official Kotlin migration skill;
- ordinary Java/JVM JPA work → language skill + `thalarch-data-sql`, and an installed focused JPA
  skill when it adds current framework-specific evidence;
- major JDK/framework migration → `thalarch-dependency` + `thalarch-java` + current primary docs and
  a focused installed migration skill when compatible.

Do not activate every JVM skill for every JVM repository.

## Platform routing

When installed and relevant, automatically consider official Antigravity/vendor platform skills
such as Kotlin/JetBrains tooling, Android, Chrome/Browser, Firebase, Modern Web, cloud/vendor SDKs,
or other curated integrations. Do not require the user to remember their names.

Platform skills supply current platform expertise; Thalarch supplies scope, causal debugging,
review, evidence, and cold verification.

## Android routing

Kotlin/Java Android work normally combines the language layer with the strongest installed Android
skills that match the task. Compose/UI work additionally uses UI/design and runtime/device evidence
as required.

## Web / visual routing

- full website, open art direction → design system + `thalarch-web-design` + best installed frontend
  design/platform skill + language overlay + browser QA + design review;
- screenshot/mockup/reference matching is central → add `thalarch-image-to-code`;
- redesign existing product → spec + existing-system audit + UI/web design + best installed redesign
  skill + browser/device QA + visual review;
- new raster image → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- precise image edit → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- inspect/compare image → `thalarch-image` + `thalarch-visual-qa`;
- exact logo/icon/diagram → `thalarch-image` + deterministic vector/code path + `thalarch-visual-qa`;
- UI with generated artwork → UI/web stack + `thalarch-imagegen` + runtime QA + visual QA.

Do not force image-first generation when visual reference creation is not actually useful.

## Risk signals

Raise risk for auth/security/privacy, shared concurrency, persistence/schema migration,
network/protocol parsing, public API/ABI/wire compatibility, build/release/signing/toolchain,
broad refactor, user data, hard-to-reproduce runtime behavior, cross-language/service interfaces,
unsafe/FFI/native code, unmeasured hot paths, architecture boundary changes, exact brand
preservation, “change only X” image edits, and production assets with exact text/transparency/
dimensions.

## Output

Return a compact routing decision:

`Mode: <...>`
`Languages/stack: <detected evidence>`
`Risk: <...>`
`Skills: <ordered minimal stack>`
`Agents: <only specialists actually needed>`
`Evidence required: <...>`
`Deferred/rejected: <only close alternatives when useful>`
