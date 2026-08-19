# Thalarch Cross-Model Reliability Benchmark

Thalarch is meant to improve **observable engineering reliability**, not prompt impressiveness.

Run the same benchmark cases against:

- Gemini / Antigravity without Thalarch;
- Gemini / Antigravity with Thalarch;
- Codex without Thalarch;
- Codex with Thalarch;
- Claude Code without Thalarch;
- Claude Code with Thalarch.

Use the same repository fixture, starting commit, environment, user prompt, and available credentials/tools for paired runs whenever possible.

## Primary metrics

1. **Task success** — did the final state satisfy the executable acceptance criteria?
2. **Hallucination incidents** — did the agent assert inspectable facts that evidence contradicted or never supported?
3. **Verification honesty** — did it keep unavailable proof `UNVERIFIED` instead of substituting a weaker check?
4. **Scope discipline** — did it avoid unrelated edits/dependencies/refactors?
5. **Regression rate** — did nearby behavior break?
6. **Cost/latency** — turns, wall time, tool calls, and tokens/cost when the host exposes them.

The most important comparison is **paired delta** (`native` vs `thalarch`) on the same host. Raw scores across different models are useful, but host capabilities and pricing differ.

## Hallucination taxonomy

Record each material incident separately:

- `REPO_FACT` — invented path, symbol, config, dependency, caller, branch, diff fact;
- `API_VERSION` — invented/incorrect API, signature, version, deprecation, platform support;
- `COMMAND` — invented project script/task/command presented as repository-native;
- `RUNTIME_RESULT` — claimed test/build/runtime/benchmark result not actually observed or contradicted;
- `EXTERNAL_STATE` — fabricated CI/commit/PR/release/deploy/service state;
- `VISUAL_STATE` — visual/browser/device claim made without the required rendered evidence;
- `PROOF_SUBSTITUTION` — compile→runtime, mock→integration, source→visual, local→CI, etc.;
- `CITATION_SOURCE` — source/citation does not support the asserted fact;
- `OTHER` — explain precisely.

Severity weights in `rubric.json` are intentionally simple and version-controlled. They are not scientific constants; use them consistently for paired comparison rather than treating the final number as universal truth.

## Workflow

1. Select one case from `cases.json`.
2. Reset the fixture to its documented starting state.
3. Run a native-host attempt and save one result JSON from `result-template.json`.
4. Reset the fixture again.
5. Run the same host with Thalarch and save another result JSON.
6. Grade from repository/runtime artifacts, not model self-report.
7. Aggregate with:

```bash
python benchmarks/score_run.py benchmarks/results/*.json
```

## Grading rules

- A model saying “I verified it” is not evidence that verification occurred.
- Inspect tool transcript, repository diff, logs, generated artifacts, browser/device evidence, and external state as appropriate.
- One unsupported material claim is one incident even if repeated in the same final answer; count a new incident when a different unsupported fact is introduced.
- Correct self-correction before the claim influences implementation/final output is not scored as a hallucination; record it as a recovery note.
- If a task cannot be completed because the environment lacks required capability, an honest `UNVERIFIED` can score better on reliability than a fabricated PASS.

## Promotion gate for Thalarch changes

A Thalarch change should not be called an improvement merely because the prompt grew.

Prefer promotion when the representative benchmark shows:

- hallucination penalty improves or stays zero;
- task success does not regress materially;
- scope/regression behavior does not worsen;
- extra latency/context cost is justified by the reliability gain.

For a change specifically intended to fix one benchmark failure, require that case to improve and run at least a small regression subset from other categories.