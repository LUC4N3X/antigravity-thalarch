---
name: thalarch-performance
description: >
  Evidence-driven performance engineering for latency, throughput, CPU, memory, startup,
  rendering, I/O, concurrency, and scalability problems. Use for explicit optimization work or
  when profiling/benchmark evidence is needed before changing a hot path.
---

# Thalarch Performance

Performance work starts with a metric and evidence, not with code that merely looks faster.

## Performance contract

Define:

- user/business-visible metric;
- workload/input distribution;
- environment;
- baseline;
- target or regression threshold;
- correctness constraints that optimization must preserve.

Examples: p95 latency, allocation rate, startup time, frame time, peak RSS, requests/sec, DB
round trips, battery/CPU budget.

## Find the bottleneck

Use the strongest available evidence for the stack:

- profiler/flame graph;
- tracing;
- benchmark;
- query plan;
- allocation/GC profile;
- browser/device performance trace;
- application metrics;
- controlled instrumentation.

Do not optimize a guessed bottleneck merely because it is visually obvious in source.

## Optimization order

Prefer high-leverage fixes:

1. eliminate unnecessary work/I/O;
2. improve algorithm/data structure;
3. batch/cache/reuse with a clear invalidation/lifetime model;
4. reduce allocations/copies/serialization;
5. improve concurrency/backpressure;
6. tune runtime/framework settings;
7. micro-optimize only when measurement still points there.

## Cache discipline

A cache requires explicit answers for:

- key identity;
- value lifetime;
- invalidation;
- size bound/eviction;
- concurrency;
- stale-data semantics;
- failure behavior.

An unbounded map is not a performance solution.

## Concurrency

More parallelism can reduce performance. Measure queueing, saturation, contention, context
switching, remote rate limits, memory pressure, and cancellation behavior.

## Benchmark quality

Avoid misleading measurements:

- warmup/runtime JIT effects;
- debug builds;
- tiny synthetic inputs unrelated to production;
- network/environment noise;
- benchmark code that optimizes away the work;
- comparing different correctness behavior.

Use the project's native benchmark/profiling ecosystem where possible.

## Verification

After the change:

- rerun the same baseline workload;
- compare the target metric and variance;
- run correctness/regression tests;
- inspect secondary costs (memory vs latency, throughput vs tail latency, startup vs steady state);
- report actual measured change, not adjectives such as “much faster”.

If reliable measurement is unavailable, mark the performance claim `UNVERIFIED`.
