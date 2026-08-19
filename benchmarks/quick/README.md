# Thalarch Quick Reliability Benchmark

This suite gives Thalarch a **real paired baseline** on Google Antigravity instead of relying on prompt impressions.

It runs the same eight deterministic, read-only repository traps twice:

1. Antigravity/Gemini with `thalarch-mode` disabled;
2. the same Antigravity/Gemini setup with `thalarch-mode` enabled and `Use Thalarch` in the prompt.

The suite targets the failure mode Thalarch cares about most: **plausible unsupported claims**.

## Why this first benchmark is read-only

The first pass deliberately avoids repository writes, builds, package installation, publication, and environment-specific toolchains. That makes native-vs-Thalarch comparison much cleaner:

- same fixture;
- same prompt;
- same model when possible;
- deterministic repository truth;
- structured output that can be scored automatically.

A later engineering suite can add mutation, tests, Java/Kotlin/Python runtime work, browser QA, and image tasks. Do not mix those into this epistemic baseline until the read-only comparison itself is stable.

## Requirements

- Python 3.10+
- authenticated Antigravity CLI `agy`
- Antigravity CLI with print mode and structured output support
- `thalarch-mode` installed as an Antigravity CLI plugin

For a controlled A/B run, `run_antigravity.py` explicitly requests the required plugin state before each phase:

- `native` -> `agy plugin disable thalarch-mode`
- `thalarch` -> `agy plugin enable thalarch-mode`

The runner trusts the exit status of those explicit commands. It does **not** infer enabled/disabled state from `agy plugin list`, because the list can describe imported packages without exposing the effective enable state in a machine-stable way.

## Infrastructure errors are not hallucinations

A CLI/parser/authentication/plugin/harness failure is not model behavior.

If Antigravity exits non-zero before producing a benchmark answer, or exits successfully without a parseable schema-conformant final result, the runner:

1. writes raw stdout/stderr;
2. prints `BENCHMARK INFRA_ERROR` and the diagnostic;
3. stops immediately;
4. records **no hallucination penalty** for that failed invocation.

Never use an infrastructure failure as evidence that native Gemini or Thalarch is better or worse.

## First probe on Windows PowerShell

From the Thalarch repository root, verify one case before spending time on the full suite:

```powershell
$RunId = Get-Date -Format "yyyyMMdd-HHmmss"

python .\benchmarks\quick\run_antigravity.py --phase native --run-id $RunId --case QH-01
python .\benchmarks\quick\run_antigravity.py --phase thalarch --run-id $RunId --case QH-01
```

If both invocations reach a real `QH-01: PASS` or `QH-01: FAIL` result rather than `BENCHMARK INFRA_ERROR`, run all eight:

```powershell
python .\benchmarks\quick\run_antigravity.py --phase native --run-id $RunId
python .\benchmarks\quick\run_antigravity.py --phase thalarch --run-id $RunId

$Results = Get-ChildItem ".\benchmarks\results\quick\$RunId\results\*.json" |
    Select-Object -ExpandProperty FullName

python .\benchmarks\score_run.py @Results
```

To pin a model, pass the **same exact model string** to both phases:

```powershell
python .\benchmarks\quick\run_antigravity.py --phase native --run-id $RunId --model "<exact model>"
python .\benchmarks\quick\run_antigravity.py --phase thalarch --run-id $RunId --model "<exact model>"
```

If model identity is unavailable or differs across the two phases, do not present the paired delta as a proven same-model effect.

## Cases

- `QH-01` — nonexistent repository symbol;
- `QH-02` — nonexistent project command;
- `QH-03` — false dependency/API premise;
- `QH-04` — temptation to claim unrun tests passed;
- `QH-05` — fabricated PR/external state;
- `QH-06` — source code substituted for rendered visual proof;
- `QH-07` — instruction-like text embedded in retrieved documentation;
- `QH-08` — stale documentation conflicting with the current manifest.

Each successful benchmark invocation saves:

- raw Antigravity `stream-json`;
- stderr;
- parsed structured answer;
- observed model when exposed;
- tool-call count when exposed;
- token usage when exposed;
- standard Thalarch benchmark result JSON.

`benchmarks/score_run.py` computes the same task/reliability/hallucination metrics used by the larger benchmark framework.

## What counts as a win

Do **not** judge success by verbosity or by whether Thalarch invokes more agents.

The paired result is interesting when Thalarch:

- reduces hallucination incidents;
- increases or preserves case pass rate;
- preserves honest `UNVERIFIED`;
- does not replace missing evidence with confidence;
- does not add unreasonable token/time cost for this small suite.

The raw trajectory remains available under `benchmarks/results/quick/<run-id>/raw/` for manual adjudication when an automatic grade looks suspicious.

## Safety

The benchmark uses plan mode, disposable fixtures in the OS temporary directory, and an explicit read-only benchmark contract. It does not authorize commit, push, PR, deployment, package installation, or external publication.

The only deliberate host-state mutation is enabling/disabling the already installed `thalarch-mode` plugin to create the requested A/B condition.

The runner does not claim that a successful CLI exit or valid JSON proves the model's factual answer. Fixture-specific grading checks the structured claims against known repository truth, and ambiguous cases should still be manually reviewed from the raw trajectory.
