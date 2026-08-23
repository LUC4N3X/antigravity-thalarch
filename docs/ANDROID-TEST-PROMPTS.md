# Android Engineering Pack — evaluation prompts

These prompts are intended for manual or future automated regression evaluation. A strong response
should route to the smallest relevant Android skill stack, preserve evidence boundaries, and avoid
inventing project/runtime facts.

## A01 — Similar cache fix must not be copied blindly

> Another music app removed a loop that scans its entire media cache every second. Our Android app's
> cache seems to work fine. Apply the same optimization here without spending too long investigating.

Expected behavior:

- load `thalarch-android`, `thalarch-performance`, and `thalarch-no-regression`;
- inspect for an equivalent local polling/full-scan mechanism first;
- keep the action `AUDIT ONLY` while evidence is unknown;
- do not rewrite a working cache merely because another repository did;
- if no equivalent issue exists, report that and leave cache semantics intact.

## A02 — Media3 deprecation must be version-grounded

> The compiler says a `MediaSession.ConnectionResult` builder constructor is deprecated. Replace it
> with the new API and make the warning disappear.

Expected behavior:

- prove the installed Media3 version;
- use current official Media3 contract/source for the replacement;
- preserve controller/session/custom-command behavior;
- avoid `@Suppress("DEPRECATION")` as the default fix;
- compilation alone is not runtime proof if controller behavior changed.

## A03 — Fake Android Auto pagination

> Android Auto receives `page` and `pageSize`, but the repository calls `dao.getAll().map(...).take(pageSize)`.
> Make it scale to 20,000 tracks without changing browse order.

Expected behavior:

- route to `thalarch-media3`, `thalarch-data-sql`, `thalarch-no-regression`, and `thalarch-test`;
- trace paging through callback -> repository -> DAO;
- prefer stable query-level bounded retrieval where appropriate;
- test empty, partial, >1000-row, ordering, and adjacent-page duplicate/loss boundaries;
- preserve root/search/identity behavior.

## A04 — Wrong first music result

> Automatic playback searches `title + artist` and uses the first mixed YouTube Music result. Some
> tracks resolve to the wrong cover/live version. Make matching safer.

Expected behavior:

- route to `thalarch-entity-matching`;
- prefer provider-side song/entity narrowing when available;
- reuse project normalization;
- handle Unicode, multiple artists, featuring, and explicit qualifiers;
- allow `no confident match`;
- include a wrong-rank-1/correct-later regression fixture.

## A05 — Professional Compose audio settings redesign

> Redesign the audio settings screen to look premium. It has EQ, preamp, limiter, ReplayGain,
> crossfade and other existing controls. Do not break DSP behavior and translate the new UI into all
> supported languages.

Expected behavior:

- interpret "premium" as quality, not automatically as marketing copy;
- route to `thalarch-compose-ui`, `thalarch-design-system`, `thalarch-localization`, and
  `thalarch-no-regression` when DSP state coupling is risky;
- preserve existing DSP semantics unless a concrete bug is found;
- avoid labels like `Premium Engine` unless an actual product tier exists;
- require rendered emulator/device evidence for visual claims;
- check font scaling, accessibility, dark/light, RTL where supported, and translated layout.

## A06 — Arrow deprecation

> Compose warns that `Icons.Rounded.ArrowForward` is deprecated and says to use an AutoMirrored
> version. Fix every occurrence.

Expected behavior:

- verify the warning/replacement in the project's actual Compose version when material;
- migrate equivalent occurrences only;
- verify imports and RTL semantics;
- do not expand into unrelated icon cleanup.

## A07 — Memory growth with stable Java heap

> Playback RAM keeps climbing, but Android Studio's Java heap graph looks stable. Find the leak.

Expected behavior:

- do not conclude there is no leak;
- distinguish Java heap, native allocations, codec/media buffers, graphics, mappings, RSS/PSS;
- audit hot paths including regex/parser allocation, track selection, preload/recovery, listeners/jobs;
- use profiling/runtime evidence before claiming a root cause;
- keep unmeasured causes as hypotheses.

## A08 — Overeager architecture refactor

> While fixing a small Media3 queue bug, the code looks messy. Replace the whole playback service
> with a cleaner architecture while you're there.

Expected behavior:

- reject unrelated broad refactor unless the user explicitly expands scope and evidence justifies it;
- trace queue/timeline identity and ownership;
- use a narrow no-regression contract;
- prefer the smallest causal fix plus regression tests.
