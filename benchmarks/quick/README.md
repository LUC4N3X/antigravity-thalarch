# Thalarch Quick Reliability Benchmark

This suite gives Thalarch a **real paired baseline** on Google Antigravity instead of relying on prompt impressions.

It runs the same eight deterministic, read-only repository traps twice:

1. Antigravity/Gemini with `thalarch-mode` disabled;
2. the same Antigravity/Gemini setup with `thalarch-mode` enabled and `Use Thalarch` in the prompt.

The suite targets the failure mode Thalarch cares about most: **plausible unsupported claims**.

## Why this first benchmark is read-only

The first pass deliberately avoids writes, network side effects, builds, package installation, and environment-specific toolchains. That makes native-vs-Thalarch comparison much cleaner:

- same fixture;
- same prompt;
- same model;
- no permission-card noise;
- no dependency/network variance;
- deterministic repository truth;
- structured output that can be scored automatically.

A later engineering suite can add mutation, tests, Java/Kotlin/Python runtime work, browser QA, and image tasks. Do not mix those into this epistemic baseline until the read-only comparison itself is stable.

## Requirements

- Python 3.10+
- Antigravity CLI `agy`
- Antigravity CLI new enough to support print mode `-p`, `--output-format stream-json`, and `--json-schema`
- authenticated Antigravity CLI
- `thalarch-mode` installed as an Antigravity plugin for the Thalarch phase

The benchmark runner **does not silently enable or disable plugins**. Plugin state is a user-level side effect and is kept explicit.

## Run on Windows PowerShell

From the Thalarch repository root:

```powershell
$RunId = Get-Date -Format "yyyyMMdd-HHmmss"

agy plugin disable thalarch-mode
python .\benchmarks\quick\run_antigravity.py --phase native --run-id $RunId

agy plugin enable thalarch-mode
python .\benchmarks\quick\run_antigravity.py --phase thalarch --run-id $RunId

python .\benchmarks\score_run.py (Get-ChildItem ".\benchmarks\results\quick\$RunId\results\*.json" | ForEach-Object FullName)
```

To pin a model, pass the **same exact model string** to both runs:

```powershell
python .\benchmarks\quick\run_antigravity.py --phase native --run-id $RunId --model "<exact model>"
python .\benchmarks\quick\run_antigravity.py --phase thalarch --run-id $RunId --model "<exact model>"
```

If you omit `--model`, the runner records the model reported by Antigravity's structured output. Do not treat a pair as valid if the two phases resolve to different models.

Re-enable Thalarch after any interrupted native run:

```powershell
agy plugin enable thalarch-mode
```

## Cases

- `QH-01` — nonexistent repository symbol;
- `QH-02` — nonexistent project command;
- `QH-03` — false dependency/API premise;
- `QH-04` — temptation to claim unrun tests passed;
- `QH-05` — fabricated PR/external state;
- `QH-06` — source code substituted for rendered visual proof;
- `QH-07` — instruction-like text embedded in retrieved documentation;
- `QH-08` — stale documentation conflicting with the current manifest.

Each run saves:

- raw Antigravity `stream-json`;
- stderr;
- parsed structured answer;
- observed model when exposed;
- tool-call count when exposed;
- token usage when exposed;
- standard Thalarch benchmark result JSON.

`benchmarks/score_run.py` then computes the same task/reliability/hallucination metrics used by the larger benchmark framework.

## What counts as a win

Do **not** judge success by verbosity or by whether Thalarch invokes more agents.

The paired result is interesting when Thalarch:

- reduces hallucination incidents;
- increases or preserves case pass rate;
- preserves honest `UNVERIFIED`;
- does not replace missing evidence with confidence;
- does not add unreasonable token/time cost for this small suite.

The raw trajectory remains available under `benchmarks/results/quick/<run-id>/raw/` for manual adjudication when an automatic regex grade looks suspicious.

## Safety

The benchmark uses `--mode=plan`, creates disposable fixtures in the OS temporary directory, and instructs the agent to work read-only. It does not authorize commit, push, PR, deployment, package installation, or external mutation.

The runner does not claim that a CLI exit code or valid JSON proves the model's factual answer. The fixture-specific grader checks the structured claims against known repository truth, and ambiguous cases should still be manually reviewed from the raw trajectory.
