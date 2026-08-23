# Android deprecation migration playbook

Use when Kotlin/Android compilation reports a deprecated AndroidX/Compose/Media3/Gradle/API symbol
or an override-signature warning that should be corrected without changing behavior.

## 1. Prove the installed version

Before choosing a replacement, inspect the actual project version from the version catalog, Gradle
build, dependency graph, or lockfile used by the repository.

Do not select a replacement from memory or from documentation for a different library version.

## 2. Prove the replacement contract

Use current official vendor documentation/source for the exact deprecated symbol and installed
version range. Confirm:

- replacement class/function/property/constructor;
- required imports;
- changed defaults;
- command/callback/state semantics;
- source/binary compatibility constraints;
- minimum SDK/toolchain requirements when material.

If the official migration contract is unclear, keep the claim `UNVERIFIED` rather than guessing.

## 3. Preserve behavior

Treat modernization and behavior change as separate concerns.

For callbacks/overrides:

- align parameter names with the supertype when named-argument compatibility warnings require it;
- preserve nullable/default semantics;
- preserve threading/lifecycle expectations.

For session/controller APIs:

- preserve available commands;
- custom commands;
- controller acceptance policy;
- connection hints/extras;
- Android Auto/external controller behavior.

For Compose directional icons, use the appropriate AutoMirrored variant when the deprecation explicitly
requires it and verify imports/RTL behavior.

## 4. Suppression is not migration

Do not use `@Suppress("DEPRECATION")` or warning flags as the default fix when a compatible modern API
exists.

Suppression is acceptable only when:

- the supported replacement is unavailable for the project's compatibility range; or
- the deprecated API is intentionally retained behind a documented compatibility boundary.

In that case, explain the reason and keep the scope narrow.

## 5. Search equivalent occurrences

After understanding the migration, search for other occurrences of the exact deprecated pattern.
Fix only equivalent safe cases within scope; do not use one warning as permission for a broad cleanup.

## 6. Proof

Run the narrowest checks that prove the migration:

- compile the affected module;
- targeted tests for changed behavior;
- lint/static checks if they surface the warning;
- emulator/device/controller behavior when the deprecation touches runtime contracts.

A warning disappearing proves only that the compiler no longer reports that warning. It does not
prove runtime behavior if the API controls sessions, services, navigation, media, or UI state.
