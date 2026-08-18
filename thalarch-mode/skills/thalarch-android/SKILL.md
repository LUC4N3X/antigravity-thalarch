---
name: thalarch-android
description: >
  Coordinates Android/Kotlin/Jetpack Compose/Gradle/Media3 work. Use for Android UI, playback,
  services, device behavior, build/toolchain, R8, testing, edge-to-edge, adaptive layout, or
  runtime debugging. Prefer official Google Android skills/CLI when installed and use device or
  emulator evidence for runtime-specific acceptance.
---

# Thalarch Android

## Android Lens

Prefer official current Android skills/tooling available in the environment.

## Preflight

Inspect:
- module graph;
- Gradle/AGP/Kotlin/version catalog;
- manifests;
- Compose/navigation/state patterns;
- CI build tasks;
- device/runtime requirements.

Do not upgrade toolchain or libraries unless the task requires it.

## Compose

Check:
- state ownership/stability;
- effects/lifecycle;
- recomposition-sensitive work;
- lazy keys;
- edge-to-edge/insets;
- adaptive behavior;
- touch targets/semantics;
- theme consistency;
- localization/truncation.

## Media/runtime

For Media3/playback/services inspect:
- lifecycle/session ownership;
- cancellation;
- buffering/retry;
- cache;
- queue/timeline invariants;
- audio focus;
- service process/state;
- resolver/network fallback ordering.

Do not cure state bugs with arbitrary delays without evidence.

## Proof hierarchy

Compilation proves compilation only.

For runtime/UI behavior use, where available:
- targeted unit/integration tests;
- instrumentation;
- emulator/device interaction;
- `adb`/log evidence;
- screenshots/recordings.
