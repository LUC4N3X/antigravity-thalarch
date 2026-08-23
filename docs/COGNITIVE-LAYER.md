# Cognitive Layer

Thalarch's Cognitive Layer adds **retrieval, durable project knowledge, experience distillation, and
teacher/evaluation feedback** around the base model without claiming to copy or retrain the model's
weights.

The objective is practical: a model working on the same kinds of engineering problems repeatedly
should not need to rediscover every verified invariant, regression pattern, or failed diagnostic path
from zero.

## Architecture

```text
REQUEST
  |
  v
CURRENT RULES + REPOSITORY + RUNTIME
  |
  +----> MEMORY RETRIEVAL -------------------------+
  |      project first, then general               |
  |      revalidate load-bearing memories          |
  |                                                v
  +------------------------------------------> CONTEXT CAPSULE
                                                   |
                                                   v
                                             SKILL ROUTING
                                                   |
                                                   v
                                                STUDENT
                                             implementation
                                                   |
                                                   v
                                           TEACHER / JUDGE
                                                   |
                                         PASS / REVISE / FAIL
                                                   |
                                                   v
                                            COLD VERIFIER
                                                   |
                                                   v
                                           EXPERIENCE CARD
                                                   |
                                                   v
                                             COMPOUND GATE
                                         /        |         \
                                    IGNORE     PROJECT     GENERAL
                                                |             |
                                                v             v
                                         PROJECT BRAIN   MEMORY STORE
```

## `thalarch-memory`

Memory uses four classes:

- `IGNORE` — noise, guesses, obvious facts, duplicates;
- `SESSION` — active-task recovery state only;
- `PROJECT` — stable repository/product knowledge;
- `GENERAL` — transferable engineering knowledge with stronger evidence/generalization.

Memory never outranks current source/runtime evidence. Retrieval is intentionally small and topical.

A portable SQLite fallback exists at:

`thalarch-mode/skills/thalarch-memory/scripts/memory_store.py`

It supports:

```text
init
add
search
list
retire
```

The fallback persists only `PROJECT` and `GENERAL` records. General memory requires `PROVEN` evidence
plus an explicit generalizability flag. Hosts with a native memory/RAG provider can use that instead,
while preserving the same evidence/privacy/freshness rules.

## `thalarch-experience`

Experience cards turn verified outcomes into reusable engineering knowledge:

```text
trigger
context
problem
proven discriminator
successful intervention
must-preserve behavior
failed alternatives
verification evidence
transfer conditions
counterexample
scope candidate
```

Negative experience is first-class: a plausible approach disproven by profiling/tests can save more
future time than a generic success note.

A single repository incident does **not** automatically become a universal rule. General promotion
requires a stable mechanism/contract, repeated independent cases, frozen evaluation/holdout evidence,
or explicit human curation.

## `thalarch-project-brain`

When repository-local durable memory is explicitly authorized, Thalarch can maintain:

```text
.thalarch/brain/
  project.md
  invariants.md
  decisions.md
  regressions.md
  playbooks.md
  design.md          # only if useful
  memory.sqlite3     # optional/local-policy dependent
```

The brain is inspectable and evidence-tagged. It does not replace source/tests/repository rules.
Load-bearing entries record scope, evidence, last verification, apply conditions, and counterexamples.

If a repository already has good architecture/ADR/runbook/design documentation, Thalarch should use
that instead of creating a competing documentation island.

## `thalarch-teacher`

The Teacher Loop evaluates the **artifact**, not the student's private reasoning:

```text
acceptance contract
+ final artifact/diff
+ fresh evidence
        |
        v
independent judge
        |
PASS / REVISE / FAIL / UNVERIFIED
```

Hard failures cannot be averaged away by a score. Scope violations, regressions, fabricated/stale
proof, weakened tests/security, or unsupported runtime/visual claims prevent a pass.

Ordinary task work is bounded to at most two targeted revision cycles by default. Persistent failure
triggers problem-model reconstruction rather than endless stylistic churn.

## Eval-driven self-improvement

Generic Thalarch changes must be harder to promote than ordinary project fixes.

Use:

1. a repeated failure class;
2. frozen evaluation cases;
3. a baseline;
4. `thalarch-autoresearch` candidate experiments;
5. unchanged correctness/honesty guardrails;
6. holdout/counterexamples;
7. independent teacher review;
8. cross-host checks when the rule is host-agnostic;
9. cold verification.

Reject grader hacking: case IDs, answer-key memorization, keyword padding, weakened rubrics, narrowed
workloads, or skipping expensive required proof are not improvements.

Machine-readable cognitive stress cases live in `benchmarks/cognitive-cases.json`.

## Memory authority order

When facts conflict:

1. explicit current user/system/repository rules;
2. current runtime/executable evidence;
3. current source/config/manifests/tests;
4. current primary/vendor contracts for version-sensitive facts;
5. verified project docs;
6. Project Brain / durable memory.

This ordering is deliberate. Memory should make the model faster at reaching the right evidence, not
more confident about stale facts.

## Privacy boundary

The Cognitive Layer is not a data vacuum.

Do not persist:

- passwords, tokens, credentials, cookies, secrets;
- private chain-of-thought;
- unnecessary sensitive personal data;
- entire private messages/logs/documents when a compact non-sensitive lesson is enough;
- proprietary third-party material when a derived engineering lesson is sufficient;
- benchmark answer keys or repository-specific hacks as general knowledge.

Creating project/user durable stores remains an explicitly authorized action.

## Example: memory-safe debugging lesson

A useful experience card is not:

> "Project X had a regex bug."

It is closer to:

```text
TRIGGER
Process memory rises during media playback while managed heap remains stable.

DISCRIMINATOR
Allocation profiling shows repeated native regex/parser work on a playback hot path.

LESSON
Inspect native/media/JNI/parser/regex allocation sources before assuming a managed-heap leak or
rewriting cache lifecycle.

COUNTEREXAMPLE
If heap analysis shows retained managed objects growing with the symptom, investigate that ownership
path directly.
```

That is useful elsewhere without blindly applying the original patch.

## What this does not claim

The Cognitive Layer does not copy another model's weights, hidden instructions, training corpus, or
private reasoning process. It improves the agent system around the model through better context,
retrieval, evidence, evaluation, and accumulated verified experience.
