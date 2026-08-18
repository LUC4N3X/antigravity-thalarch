# Thalarch 2.0 — Design Notes

## Goal

Thalarch is designed as a project-agnostic engineering harness for Google
Antigravity. The core must not assume a particular language, framework, product,
repository layout, operating system, or user.

Domain knowledge is layered through focused skills and loaded only when relevant.

## Progressive disclosure

Version 1 concentrated most behavior in one high-rigor skill. Version 2 introduces
a router plus focused process/domain skills so Antigravity can use the smallest
instruction set that safely fits the task.

This is both a quality and context-efficiency decision: unused expertise should
not compete with the current problem for attention.

## Structural enforcement

The primary orchestrator intentionally has no project write tools and no shell
command tool.

- planners/researchers/debuggers establish evidence;
- implementers mutate;
- reviewers inspect independently;
- the verifier judges acceptance from a cold context.

The separation is more important than role names. It prevents the coordinator
from casually implementing and self-approving the same change.

## Risk-sized review council

Review depth is proportional to risk:

- **lite** — general reviewer for a small bounded diff;
- **standard** — spec/correctness review plus ordinary engineering quality;
- **deep** — independent security, performance/concurrency, and domain lenses as relevant.

More reviewers are not inherently better. Irrelevant review lenses create noise
and false positives.

## Causal debugging

Unexpected behavior is treated as an investigation problem before it is treated
as an editing problem. A root-cause hypothesis should make a prediction and name
what would disprove it.

After repeated disproven hypotheses, the protocol reassesses assumptions and
architecture rather than accumulating patches.

## Evidence hierarchy

Thalarch separates claims by what the evidence can actually prove:

- lint does not prove compilation;
- compilation does not prove runtime behavior;
- unit tests do not prove cross-service integration;
- a screenshot does not prove interaction;
- an implementer report does not prove acceptance.

`PASS`, `FAIL`, and `UNVERIFIED` remain intentionally distinct.

## Knowledge compounding

Difficult tasks may yield reusable lessons, but Thalarch keeps them ephemeral by
default. A lesson becomes durable repository documentation only when the user or
project explicitly chooses a knowledge sink.

This prevents permanent rule files from filling with task-specific noise.

## External actions

The protocol distinguishes local implementation from consequential external
side effects. Commit/push/PR, merge, publish/release, deployment, permission
changes, and destructive operations are separate authorization classes.

An optional command hook can harden this boundary, but it is disabled by default
because hooks can affect every session using the plugin.

## Self-evaluation

Thalarch ships representative eval prompts because prompt size and agent count are
poor proxies for quality.

Changes should be measured against:

- routing accuracy;
- unnecessary ceremony;
- scope discipline;
- root-cause-before-fix compliance;
- acceptance coverage;
- review false-positive rate;
- verification honesty;
- external-action discipline;
- context/turn cost;
- cross-project portability.

A longer prompt that does not improve behavior is a regression.
