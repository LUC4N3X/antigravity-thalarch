---
name: thalarch-router
description: >
  Chooses the smallest compatible process, language, and domain skill stack for a software or
  visual task. Use before complex work, when multiple skills could apply, or when the agent must
  distinguish bug, feature, architecture, refactor, performance, API/data, Java, Kotlin, Python,
  TypeScript, Go, Rust, UI/image, Android, security, CI, Git, and review workflows.
---

# Thalarch Router

Classify before loading heavy instructions.

## Decision

1. Identify the task's primary goal/failure type.
2. Detect the project language/runtime/toolchain from repository evidence.
3. Estimate risk: low / medium / high.
4. Identify evidence needed for completion.
5. Select the smallest process + language + domain stack that covers the task.
6. Prefer process skills before domain/language execution skills.
7. Prefer official current platform skills when installed and relevant.
8. Do not load unrelated skills “just in case”.
9. For image inputs/outputs, classify inspect/generate/edit/vector/capture/compare/annotate/optimize.

## Core process routing

- small safe edit → `thalarch-code-craft` + lightweight `thalarch-review`;
- bug/regression → `thalarch-debug` + language overlay + `thalarch-test` + review;
- feature → `thalarch-spec` + language overlay + `thalarch-test` + review;
- architecture → `thalarch-spec` + `thalarch-codebase-intel` + relevant domain/language + deep review;
- refactor → `thalarch-refactor` + language overlay + `thalarch-test` + review;
- performance → `thalarch-performance` + language overlay + performance review;
- API/service boundary → language overlay + `thalarch-api` + security/data skills as relevant;
- database/ORM/migration → language overlay + `thalarch-data-sql` + test/review;
- dependency/toolchain change → `thalarch-dependency` + affected language/domain + broad compatibility verification;
- security → `thalarch-security` + relevant language/domain + review council;
- CI → `thalarch-ci` + language/toolchain overlay + security when relevant;
- Git/publication → `thalarch-git` + review + remote-state verification.

`thalarch-code-craft` is the default universal coding overlay for meaningful code mutation/review.

## Language detection and routing

Use source files plus build manifests. Do not infer from repository name alone.

- Java (`.java`, Maven/Gradle JVM Java source) → `thalarch-java` / `thalarch-java-engineer`;
- Kotlin (`.kt`, `.kts`, Kotlin Gradle plugins) → `thalarch-kotlin` / `thalarch-kotlin-engineer`;
- Python (`.py`, `pyproject.toml`, Python package metadata) → `thalarch-python` / `thalarch-python-engineer`;
- TypeScript/JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`, package scripts) → `thalarch-typescript` / `thalarch-typescript-engineer`;
- Go (`.go`, `go.mod`) → `thalarch-go` / `thalarch-go-engineer`;
- Rust (`.rs`, `Cargo.toml`) → `thalarch-rust` / `thalarch-rust-engineer`.

For mixed-language changes, choose the minimum set that covers the changed boundary. Use separate
specialists when two languages have independent implementation surfaces; use an explicit
integration stage for their shared contract.

If no dedicated language skill exists, apply `thalarch-code-craft`, project-native conventions,
and primary documentation for version-sensitive APIs.

## Android routing

Kotlin/Java Android work normally combines the language overlay with `thalarch-android`.
Compose/UI work additionally uses `thalarch-ui` and runtime/device evidence as required.

## Web / visual routing

- full website → `thalarch-design-system` + `thalarch-web-design` + language/frontend overlay + `thalarch-browser-qa` + design review;
- UI redesign → `thalarch-spec` + `thalarch-ui` + language overlay + browser/device QA + visual review;
- new raster image → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- precise image edit → `thalarch-image` + `thalarch-imagegen` + `thalarch-visual-qa`;
- inspect/compare image → `thalarch-image` + `thalarch-visual-qa`;
- exact logo/icon/diagram → `thalarch-image` + deterministic vector/code path + `thalarch-visual-qa`;
- UI with generated artwork → UI/web stack + `thalarch-imagegen` + runtime QA + visual QA.

## Risk signals

Raise risk for:

- auth/security/privacy;
- concurrency/shared mutable state;
- persistence/schema migration;
- networking/protocol parsing;
- public API/ABI/wire-format compatibility;
- build/release/signing/toolchain;
- broad refactor;
- user data;
- runtime behavior difficult to reproduce;
- cross-language or cross-service interfaces;
- unsafe/FFI/native code;
- performance hot paths with weak measurement;
- exact visual identity/brand preservation;
- “change only X” image edits;
- production assets with exact text/transparency/dimensions.

## Output

Return a compact routing decision:

`Mode: <...>`
`Languages: <detected from evidence>`
`Risk: <...>`
`Skills: <ordered minimal stack>`
`Agents: <only specialists actually needed>`
`Evidence required: <...>`
`Why not other skills: <only meaningful exclusions>`
