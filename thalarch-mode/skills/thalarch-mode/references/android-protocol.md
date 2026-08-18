# Android / Compose / Gradle Protocol

Use for Android, Kotlin, Jetpack Compose, Media3, Gradle, AGP, AndroidX, device
behavior, or Play/F-Droid build work.

## Repository-first

Before suggesting commands or APIs:

- read `settings.gradle*`, root/module `build.gradle*`, version catalogs;
- inspect `gradle.properties` and relevant manifests;
- read project rules and CI workflows;
- identify exact modules touched;
- inspect existing Compose/state/navigation patterns before adding new ones.

Do not upgrade Gradle, AGP, Kotlin, AndroidX, Media3, compileSdk/targetSdk, or
plugins unless the task requires it.

## Compose

Check:

- state ownership and stability;
- recomposition-sensitive work;
- keys for lazy content;
- side effects (`LaunchedEffect`, `DisposableEffect`, lifecycle);
- remember/saveable correctness;
- insets/edge-to-edge;
- accessibility semantics and touch targets;
- previews/screenshots when useful;
- theme consistency and dynamic color behavior.

## Media / playback

For Media3 or playback logic, inspect:

- player lifecycle;
- buffering/retry behavior;
- cancellation;
- cache interaction;
- audio focus;
- service/session state;
- timeline/queue invariants;
- network error codes and fallback ordering.

Do not mask resolver/playback failures with arbitrary delays if a contract or
state transition can be fixed at the source.

## Verification

Use the repository's own commands first.

Possible checks, only when they actually exist in the project:

- targeted Kotlin/unit tests;
- module compile task;
- app assemble task;
- lint/static analysis;
- instrumentation/device test;
- `adb logcat` reproduction for runtime-only failures.

Never claim an Android UI/runtime bug is fixed solely from successful compilation
when the acceptance criterion depends on real device behavior.
