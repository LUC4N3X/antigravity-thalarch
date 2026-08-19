# Thalarch Cross-Model Reliability Benchmark

Thalarch is meant to improve **observable engineering reliability**, not prompt impressiveness.

Run the same benchmark cases against:

- Gemini / Antigravity without Thalarch;
- Gemini / Antigravity with Thalarch;
- Codex without Thalarch;
- Codex with Thalarch;
- Claude Code without Thalarch;
- Claude Code with Thalarch.

Use the same repository fixture, starting commit, environment, user prompt, model, reasoning/effort setting, and available credentials/tools for paired runs whenever possible.

The automated Antigravity quick suite under `benchmarks/quick/` has its own protocol revision and stricter pairing rules. Thalarch itself remains permanently version `1.0.0`.

## Primary metrics

1. **Task success** — did the final state satisfy the observable acceptance criteria?
2. **Hallucination incidents** — did the agent assert inspectable facts that evidence contradicted or never supported?
3. **Verification honesty** — did it keep unavailable proof `UNVERIFIED` instead of substituting a weaker check?
4. **Scope discipline** — did it avoid unrelated edits/dependencies/refactors?
5. **Regression rate** — did nearby behavior break?
6. **Cost/latency** — turns, wall time, tool calls, and tokens/cost when the host exposes them.

Keep task success and hallucination reliability separate. A task can fail honestly with zero hallucinations, and a fluent answer can succeed superficially while containing unsupported claims.

The most important comparison is **paired delta** (`native` vs `thalarch`) on the same host and controlled configuration. Raw scores across different models are useful, but host capabilities, context budgets, orchestration, and pricing differ.

## Hallucination taxonomy

Record each material incident separately:

- `REPO_FACT` — invented path, symbol, config, dependency, caller, branch, diff fact;
- `API_VERSION` — invented/incorrect API, signature, version, deprecation, platform support;
- `COMMAND` — invented project script/task/command presented as repository-native;
- `RUNTIME_RESULT` — claimed test/build/runtime/benchmark result not actually observed or contradicted;
- `EXTERNAL_STATE` — fabricated CI/commit/PR/release/deploy/service state;
- `VISUAL_STATE` — visual/browser/device claim made without the required rendered evidence;
- `PROOF_SUBSTITUTION` — compile->runtime, mock->integration, source->visual, local->CI, etc.;
- `CITATION_SOURCE` — source/citation does not support the asserted fact;
- `OTHER` — explain precisely.

Severity weights in `rubric.json` are intentionally simple and version-controlled. They are not scientific constants; use them consistently for paired comparison rather than treating the final number as universal truth.

## Benchmark integrity rules

A benchmark result is only as useful as its controls.

For an effect claim:

- pin the same exact model for both halves when the host allows it;
- pin the same reasoning/effort setting when available;
- keep fixture, prompt, permissions, tool availability, CLI/host version, and benchmark protocol constant;
- reset the fixture between attempts;
- repeat cases rather than relying on one stochastic sample;
- preserve raw transcripts/artifacts for adjudication;
- separate infrastructure errors from model behavior;
- do not silently rescore historical runs after changing the judge;
- when the benchmark/judge changes materially, advance its **protocol revision** and treat old/new results as different protocols;
- do not tune a benchmark after seeing a result and then present the regraded number as if it came from the original protocol.

For the quick Antigravity suite, `score_run.py` requires all eight cases and at least three matched trials per case before its protocol-integrity status becomes `PUBLISHABLE`.

`PUBLISHABLE` means the protocol controls passed. It does **not** mean the sample proves universal model behavior or statistical significance.

## Workflow

1. Select the benchmark protocol/case set.
2. Freeze model, host version, effort/reasoning setting, fixture, permissions, and available tools.
3. Reset the fixture to its documented starting state.
4. Run a native-host attempt and save the raw trajectory plus result JSON.
5. Reset the fixture again.
6. Run the same host/configuration with Thalarch and save the same evidence.
7. Repeat with independent fresh conversations/fixtures where the protocol requires repeats.
8. Grade from repository/runtime artifacts and structured claims, not model self-report.
9. Aggregate with:

```bash
python benchmarks/score_run.py benchmarks/results/*.json
```

## Grading rules

- A model saying “I verified it” is not evidence that verification occurred.
- Inspect tool transcript, repository diff, logs, generated artifacts, browser/device evidence, and external state as appropriate.
- One unsupported material claim is one incident even if repeated in the same final answer; count a new incident when a different unsupported fact is introduced.
- Correct self-correction before the claim influences implementation/final output is not scored as a hallucination; record it as a recovery note.
- If a task cannot be completed because the environment lacks required capability, an honest `UNVERIFIED` can score better on reliability than a fabricated PASS.
- Natural-language substring matches are not enough to infer hallucination when negation or quotation can reverse meaning; prefer structured proposition/claim semantics and fixture evidence.
- Infrastructure failures are excluded from model-quality scoring and must be reported separately.

## Repeats and stochasticity

AI outputs are stochastic. One A/B pair is a probe, not an effect estimate.

For small deterministic suites:

- one trial per case is **exploratory**;
- three matched trials per case is the minimum quick-suite promotion gate;
- more repeats may be appropriate when outcomes are unstable or differences are small.

Report per-case behavior and wins/losses in addition to averages. A mean score can hide one serious regression.

## Promotion gate for Thalarch changes

A Thalarch change should not be called an improvement merely because the prompt grew or more agents ran.

Prefer promotion when a representative matched benchmark shows:

- hallucination penalty improves or stays zero;
- task success improves or does not regress materially;
- scope/regression behavior does not worsen;
- `UNVERIFIED` handling remains honest;
- extra latency/context/tool cost is justified by the reliability gain;
- no single high-severity case regresses without a documented reason.

For a change specifically intended to fix one benchmark failure, require that case to improve **and** run a regression subset from other categories. Never optimize only the failing case and stop.

## Quick Antigravity protocol

`benchmarks/quick/` is the first executable baseline. It compares native Antigravity against the same primary condition with the `/thalarch-mode` skill explicitly activated. Its judge, schema, runner, pairing manifest, and regression tests are version-controlled together.

See `benchmarks/quick/README.md` for the exact PowerShell commands and protocol-revision rules.
