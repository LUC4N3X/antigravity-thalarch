# Debugging Protocol

Use this only for bugs, crashes, build/test failures, regressions, flaky behavior,
performance anomalies, or unexpected runtime state.

## 1. Reproduce

Capture the smallest reliable reproduction:

- exact steps or command;
- expected result;
- actual result;
- relevant environment/version;
- frequency if intermittent.

If the failure is intermittent, do not convert "sometimes" into a deterministic
story. Instrument and collect evidence.

## 2. Locate the failing boundary

Trace the data/control flow across components. At each boundary, establish:

- what enters;
- what exits;
- relevant state/configuration;
- whether the contract is satisfied.

For multi-layer systems, prefer one diagnostic run that tells you **where** the
failure begins over several speculative edits.

## 3. Compare against a working path

Find the closest analogous code that works. Compare behavior, not just syntax.

List meaningful differences before choosing a fix.

## 4. State one falsifiable hypothesis

Format:

`Hypothesis: <cause> because <evidence>.`
`Disproof: <observation/test that would make this false>.`

Test one variable at a time.

## 5. Fix the source

Prefer correcting the earliest incorrect state or broken contract rather than
adding downstream retries, null guards, delays, or conditionals that hide it.

Retries/timeouts are valid only when evidence shows the cause is genuinely
external, timing-dependent, or recoverable.

## 6. Regression proof

Where practical:

- demonstrate the failing case before the fix;
- apply the minimal fix;
- demonstrate the same case passing;
- run nearby regression checks.

## Breaker rule

After three failed fix hypotheses:

1. stop adding patches;
2. re-open assumptions;
3. ask a fresh debugger/planner to inspect architecture and shared state;
4. identify whether the current design itself is the source of repeated failure.

Do not attempt an endless fourth/fifth "tiny fix" chain.
