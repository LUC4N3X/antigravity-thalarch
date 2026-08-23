# Android performance and hot-path audit

Use this reference with `thalarch-android` + `thalarch-performance` when a Kotlin/Android task
mentions memory growth, cache overhead, playback churn, UI jank, CPU use, battery, allocations, or
unnecessary periodic work.

## Principle

Do not optimize source that merely looks suspicious. First determine whether the code runs on a hot
path and whether the cost is observable or plausibly large enough to matter.

For a currently working cache or playback subsystem, also load `thalarch-no-regression`.

## Hot-path audit checklist

Look for evidence of:

- `Regex(...)` or `Pattern.compile(...)` inside frequently called functions;
- JSON/parser/formatter objects recreated per frame/item/callback;
- repeated Unicode normalization/tokenization of stable strings;
- `.map`, `.filter`, `.sorted*`, `.groupBy`, `.associate*` over large collections on every emission;
- polling loops using `while (isActive)` + `delay(...)` when an event/Flow/invalidation exists;
- periodic enumeration of all `SimpleCache` keys/spans;
- full database scans used only to compute a small changed subset;
- repeated `DataStore.data.first()` / preference reads in hot loops;
- Room queries launched per item (N+1);
- Flows recreated/subscribed repeatedly instead of shared at the correct lifetime;
- coroutines/jobs/listeners that outlive their owner or get registered more than once;
- bitmap/artwork decode/resizing above display needs;
- expensive work directly inside frequently recomposed composables;
- unstable lazy-list keys or state causing broad recomposition;
- JNI/native allocation churn hidden from Java heap observations;
- video decoders/tracks active during intended audio-only playback;
- duplicate preload/download/cache work for the same identity;
- unbounded retry/recovery loops;
- concurrency that increases memory pressure or downstream contention instead of throughput.

## Cache mutation gate

Before changing a cache, answer:

- What is the cache key identity?
- What owns the cache?
- What invalidates an entry?
- What is the size/eviction policy?
- What reads/writes it concurrently?
- What stale-data behavior is allowed?
- Which playback/download/offline paths depend on it?

**Existing cache behavior is presumed correct until a reproducible inefficiency or correctness bug is
demonstrated. Audit first. Mutate second.**

If another project removed polling, do not assume this project has equivalent polling. Search for
the actual mechanism and prove the similarity before porting the idea.

## Measurement

Prefer the strongest available evidence:

- Android Studio profiler;
- allocation/native-memory profiling;
- Perfetto/system trace;
- Macrobenchmark/Microbenchmark when already appropriate;
- `adb` process/memory/log evidence;
- controlled counters/logging;
- comparable before/after workload.

For playback memory, distinguish where possible:

- Java/Kotlin heap;
- native allocations;
- graphics/bitmap memory;
- codec/media buffers;
- mapped/cache/file-backed memory;
- total process RSS/PSS.

A stable Java heap does not prove stable native/media memory.

## Comparable-workload rule

Use the same meaningful scenario before and after, including:

- same build type;
- same device/emulator class;
- same input/media where practical;
- same cache warm/cold state;
- same duration;
- same playback/UI mode.

Do not report percentages from incomparable runs.

## Optimization preference order

1. eliminate unnecessary periodic work;
2. move from full scan to targeted invalidation/event/Flow;
3. fix query shape/N+1;
4. cache/reuse immutable expensive objects with explicit lifetime;
5. reduce allocation/copy churn;
6. bound retries/preload/concurrency;
7. tune implementation only after measurement still points there.

## Regression proof

After a performance change, verify the adjacent correctness contract. For playback/cache this often
includes cached and uncached playback, seek, next/previous, offline/download interaction, eviction,
prefetch, recovery, long playback, and memory stability.
