---
name: thalarch-skill-intelligence
description: >
  Autonomous skill-selection layer for Thalarch. Use at the start of non-trivial work and again
  after project discovery when the available skill catalog may contain stronger project-local,
  official platform, Thalarch, or third-party expertise. Shortlists and activates the smallest
  high-value skill stack based on task fit, project/toolchain compatibility, authority/currentness,
  tool leverage, evidence needs, redundancy, conflicts, and context cost.
---

# Thalarch Skill Intelligence

Antigravity exposes available skills to the agent by name and description. Use that inventory as
a capability catalog instead of requiring the user to name every useful skill manually.

The goal is **best-fit expertise, not maximum skill count**.

## 1. Automatic discovery pass

For every non-trivial task, before deep exploration or mutation:

1. inspect the available skill names/descriptions exposed by the current Antigravity session;
2. inspect applicable project-local skills and repository rules;
3. infer the task phase, language/runtime, framework/platform, risk, and evidence needs;
4. shortlist only skills whose descriptions materially match one of those dimensions;
5. read the full instructions only for shortlisted candidates;
6. choose the smallest compatible stack that covers the task.

Do not wait for the user to say “use skill X” when a clearly relevant installed skill already
exists.

Do not read every installed `SKILL.md` just because it is available. Discovery metadata exists to
avoid context pollution.

## 2. Re-route after evidence

Initial routing is provisional.

After repository preflight reveals the actual stack, versions, framework, runtime, or problem
mechanism, repeat the selection pass when that evidence could change the best skill set.

Examples:

- generic Kotlin becomes Kotlin + Android + an official Android testing skill after Gradle/manifest
  evidence confirms an Android app;
- generic frontend becomes TypeScript + project-local React guidance + Browser/Chrome tooling after
  the package graph is known;
- generic Python becomes Python + FastAPI/API/data skills only after those dependencies are proven;
- a suspected performance issue may drop the performance skill if root-cause evidence shows the
  problem is actually correctness/configuration.

Skills may be removed as well as added.

## 3. Selection priority

Evaluate candidates in this order of authority, while still requiring task fit:

1. **Explicit user constraints and repository rules** — these are not optional skill suggestions.
2. **Project/workspace-local skill** with direct knowledge of the current repository/workflow.
3. **Official platform/vendor skill** matching the actual technology/version when available.
4. **Thalarch process/language/domain skill** that supplies orchestration, verification, or a
   missing engineering lens.
5. **Trusted third-party/community skill** when it is more specific or useful than the generic
   fallback and does not conflict with stronger sources.
6. **Generic fallback reasoning** when no suitable skill exists.

A higher-authority skill does not win merely because of its source if it is irrelevant to the
actual task.

## 4. Candidate scoring

For each serious candidate, reason over these dimensions:

- **Task fit** — does it directly address the current operation/problem?
- **Project specificity** — does it understand this repository/framework/workflow?
- **Version compatibility** — is its guidance compatible with the runtime/library/toolchain in use?
- **Authority/currentness** — project-owned or official/current guidance beats stale generic memory.
- **Tool leverage** — does it unlock a real tool, browser, device, profiler, generator, MCP, or
  deterministic script that improves evidence?
- **Evidence leverage** — does it improve the ability to prove the acceptance criterion?
- **Complementarity** — does it add a missing lens rather than duplicate another loaded skill?
- **Context cost** — how much instruction/context will it consume relative to its value?
- **Conflict risk** — could its style/process rules contradict stronger project or user constraints?

Select the highest-value compatible set, not every candidate with a positive score.

## 5. Skill-stack shape

A normal engineering stack should usually contain only:

- one process skill (debug/spec/refactor/performance/etc.);
- one language skill when useful;
- zero to two domain/platform skills;
- one verification/review path.

Complex high-risk work may exceed this when independent concerns genuinely require it.

Avoid “skill soup”. If two skills cover the same concern, choose the more project-specific,
current, evidence-producing one unless the second adds a distinct capability.

## 6. Official/platform specialization

When installed and relevant, prefer current official platform skills for platform-specific facts
and workflows — for example Android, Chrome/Browser, Firebase, cloud/vendor SDKs, or other curated
Antigravity integrations.

Thalarch remains the orchestration/quality layer around them. Do not copy their entire guidance
into Thalarch when Antigravity can load the official skill directly.

## 7. Project-local skills

Treat `.agents/skills` (and supported workspace skill locations) as high-value candidates because
they can encode repository-specific build, test, deploy, architecture, or style rules.

Before trusting one blindly, check that its scope still matches the current project state. A stale
project skill can be less reliable than current repository configuration.

## 8. Missing capability

If no installed skill adequately covers a high-value domain:

- use `thalarch-researcher` and current primary documentation to fill the knowledge gap;
- if web research discovers a potentially useful external skill/plugin, report it as an optional
  capability rather than silently installing it unless the current request authorizes installation
  or customization changes;
- never fabricate a skill name or pretend a missing skill was loaded.

## 9. Conflict resolution

When loaded guidance conflicts, resolve in this order:

1. platform/system safety constraints;
2. explicit current user instruction;
3. repository/project rules and exact build/runtime contracts;
4. current official platform/vendor guidance for the proven version;
5. Thalarch acceptance/safety/verification invariants;
6. third-party/general style guidance.

Do not let a community style skill override a repository's established conventions or an explicit
scope constraint.

## 10. Skill-selection ledger

For non-trivial work keep a compact internal/working record:

- `Selected:` skill → why it materially helps;
- `Rejected:` only close alternatives → why redundant/incompatible/lower-value;
- `Deferred:` skill → condition that would make it relevant later.

Do not spam the user with the full candidate list. Surface the final stack when useful or when the
user asks how Thalarch routed the task.

## 11. Failure modes

Never:

- load all skills for “maximum power”;
- prefer a skill because its name sounds expert;
- use a language/framework skill before confirming the stack;
- keep a skill active after evidence shows it is irrelevant;
- duplicate official platform guidance into the main prompt when it can be loaded on demand;
- install third-party skills without authorization;
- treat skill activation as proof that the task was executed correctly.

A skill is guidance. Fresh repository/runtime evidence remains the authority for completion.
