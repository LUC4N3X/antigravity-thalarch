---
name: thalarch-compound
description: >
  Extracts reusable, verified engineering knowledge after difficult tasks so future work gets
  cheaper. Use after a non-trivial bug fix, architecture discovery, recurring failure, or review
  that revealed a stable repository invariant. Never persist guesses or task-specific noise.
---

# Thalarch Compound

A completed task may contain knowledge worth keeping.

## Candidate lesson

A lesson qualifies only if:
- supported by evidence from this run;
- likely to matter again;
- not obvious from ordinary code reading;
- stable enough to outlive this task.

Examples:
- a hidden build/test prerequisite;
- an ownership/lifecycle invariant;
- a recurring integration contract;
- a reliable diagnostic command;
- a repository-specific convention;
- a failure pattern and its proven discriminator.

## Distill

Store, by default, only in the current work artifact/ledger.

Do not modify `AGENTS.md`, `GEMINI.md`, docs, or repository rules unless the user
requested durable documentation or the task explicitly includes it.

Write lessons as:
`Context → invariant/lesson → evidence → when to apply → when NOT to apply`.

Delete weak lessons. Knowledge bloat is also debt.
