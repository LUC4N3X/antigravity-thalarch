# Android Engineering Pack

Thalarch's Android layer is designed for real application work where a correct-looking patch can
still break playback, cache behavior, browsing, UI state, accessibility, or localization.

The pack stays project-agnostic and is automatically copied to Codex and Claude Code by the existing
adapter installer because all canonical `thalarch-*` skills are installed from `thalarch-mode/skills`.

## Core routing

`thalarch-android` remains the coordinator. It selects only the specialist surfaces needed by the
actual repository/task.

### `thalarch-media3`

Use for AndroidX Media3 / ExoPlayer work involving:

- `MediaSession` / `MediaLibrarySession`;
- `MediaSessionService` / `MediaLibraryService`;
- controller/session commands;
- Android Auto browsing;
- queue/timeline identity;
- `playWhenReady` vs transient `isPlaying` state;
- audio-only vs video track selection;
- cache, preload, recovery, and cancellation;
- `DefaultAudioSink` / `AudioProcessor` pipelines;
- version-sensitive Media3 deprecations.

The skill requires an ownership/lifecycle map before architectural mutation and treats runtime
controller/player behavior as a runtime claim rather than something compilation can prove.

### `thalarch-compose-ui`

Use for Jetpack Compose redesigns and product UI work.

It combines:

- existing-design extraction before invention;
- state/recomposition discipline;
- adaptive layout;
- accessibility and 48dp-class touch targets;
- TalkBack semantics;
- font scaling;
- RTL and AutoMirrored directional icons;
- dark/light/dynamic color;
- localization-aware layout;
- actual emulator/device render inspection.

It also rejects generic AI-dashboard aesthetics and fake prestige/marketing labels in functional
settings screens when no real product tier exists.

### `thalarch-entity-matching`

Use for automatic fuzzy identity resolution such as:

- title + artist → playable provider item;
- album → remote catalog entity;
- product → catalog record;
- other search-result binding where near-duplicates exist.

Key rules:

- narrow provider-side result type first when possible;
- reuse existing project normalization;
- handle Unicode rather than ASCII-only assumptions;
- preserve explicit qualifiers such as live/remix when they express user intent;
- score load-bearing fields separately;
- allow `no confident match` instead of silently accepting rank 1;
- test ambiguity and wrong-first-result cases.

### `thalarch-localization`

Use whenever user-facing strings change.

It verifies:

- real locale inventory;
- key parity;
- placeholder/plural compatibility;
- natural technical terminology;
- layout expansion;
- RTL;
- representative rendered locales.

A default-locale build is explicitly not treated as localization proof.

### `thalarch-no-regression`

Use before risky mutation of a subsystem that currently works.

The compact contract records:

```text
SURFACE
Must preserve
Suspected problem
Evidence state
AUDIT ONLY vs TARGETED MUTATION
Verification required
```

If the suspected problem remains `UNKNOWN`, the default action is audit, not rewrite. A similar fix
in another repository is treated as a lead to investigate rather than proof that the local project
has the same defect.

## Android performance reference

`thalarch-android/references/android-performance.md` adds an Android-specific hot-path audit for:

- repeated regex compilation;
- JSON/formatter/parser churn;
- collection-wide transforms on every emission;
- polling loops;
- full `SimpleCache` scans;
- Room N+1 queries;
- repeated DataStore reads;
- Flow/listener/job lifetime mistakes;
- bitmap/artwork over-allocation;
- Compose recomposition cost;
- native/JNI/media allocation churn;
- unnecessary video decoding during audio-only playback;
- duplicate preload/recovery work.

For a working cache, the pack uses the rule:

> Existing cache behavior is presumed correct until a reproducible inefficiency or correctness bug
> is demonstrated. Audit first. Mutate second.

## Room / Android Auto pagination reference

`thalarch-android/references/room-pagination.md` traces pagination end-to-end:

```text
page/pageSize
  -> Media3/UI callback
  -> repository
  -> DAO/data source
  -> LIMIT/OFFSET or native bounded retrieval
  -> stable ordered result
```

It explicitly rejects loading a full large dataset and calling `.take(pageSize)` as fake pagination.
The boundary matrix covers empty, partial, beyond-end, pageSize 1, >1000 rows, ordering ties, and
adjacent-page duplicate/loss checks.

## Deprecation migration reference

`thalarch-android/references/deprecation-migration.md` requires:

1. the real installed dependency version;
2. the exact official replacement contract;
3. minimal behavior-preserving migration;
4. equivalent-occurrence search only after the migration is understood;
5. compile/test/runtime proof at the layer the API actually controls.

`@Suppress("DEPRECATION")` is not accepted as the default migration strategy when a compatible
supported API exists.

## Recommended stacks

### Media player reliability

```text
thalarch-context
thalarch-codebase-intel
thalarch-kotlin
thalarch-android
thalarch-media3
thalarch-no-regression
thalarch-test
```

Add `thalarch-performance` only when performance/memory/cache evidence is material.

### Android Auto pagination

```text
thalarch-android
thalarch-media3
thalarch-data-sql
thalarch-no-regression
thalarch-test
```

### Music/provider matching

```text
thalarch-android
thalarch-entity-matching
thalarch-test
```

### Professional Compose settings redesign

```text
thalarch-android
thalarch-compose-ui
thalarch-design-system
thalarch-localization
thalarch-test
```

### AndroidX/Media3 deprecation cleanup

```text
thalarch-android
thalarch-source-grounding
thalarch-media3   # when Media3 is the affected contract
thalarch-test
```

## Evidence philosophy

The pack preserves the core Thalarch hierarchy:

- source inspection can prove structure;
- compilation can prove signatures/types;
- unit tests can prove local contracts;
- integration tests can prove connected boundaries;
- device/emulator/controller evidence is required for runtime behavior;
- rendered pixels/interaction are required for visual claims;
- profiling/trace evidence is required for measured performance claims.

When the required layer cannot be exercised, the result remains `UNVERIFIED` rather than being
promoted by confidence.
