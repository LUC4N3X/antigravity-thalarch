<div align="center">

<img src="assets/branding/thalarch-banner.webp" alt="Thalarch" width="100%" />

<strong>Anti-hallucination engineering layer for Gemini on Google Antigravity.</strong><br/>
<sub>Built first for Gemini inside Antigravity: repository inspection, version grounding, specialist routing, independent review, and real evidence before “done”.</sub>

[![Version](https://img.shields.io/badge/Version-1.0.0-4F6B5F?style=flat-square)](#permanent-version-policy)
[![Focus](https://img.shields.io/badge/Focus-Anti--hallucination-8B6F47?style=flat-square)](#why-thalarch)
[![License: MIT](https://img.shields.io/badge/License-MIT-2F6B66?style=flat-square)](LICENSE)
[![Hosts](https://img.shields.io/badge/Hosts-Antigravity%20%C2%B7%20Codex%20%C2%B7%20Claude-5D6B8A?style=flat-square)](#one-core-three-hosts)
[![Validation](https://github.com/LUC4N3X/antigravity-thalarch/actions/workflows/validate.yml/badge.svg)](.github/workflows/validate.yml)

<sub>Codex and Claude Code adapters included too · Inspect first · Verify what matters · Never turn confidence into fake proof.</sub>

</div>

## Why Thalarch?

A coding model can be very capable and still make familiar engineering mistakes: assume the wrong framework version, skip repository rules, patch the symptom instead of the cause, over-edit a project, or declare success without proving the result.

**Thalarch wraps the model in a stricter engineering process.** It does not try to make the underlying model sound smarter. It tries to make the work **more deliberate, more grounded, and easier to trust**.

It pushes the agent to:

- **understand the repository before editing it;**
- **choose the smallest useful skill stack** instead of activating everything blindly;
- **prove version-sensitive facts** against the real project and current primary sources;
- **route work to the right specialist** for language, architecture, debugging, security, data, performance, or visual tasks;
- **keep diffs narrow and repository-native;**
- **review independently and finish with evidence** that actually matches the claim.

> **Confidence is not proof.** If the required evidence is unavailable, Thalarch is expected to say so.

---

## Benchmark · proof, not promises

<div align="center">

### **100% task pass · 100% hallucination-free · +16.7 pp vs Native**

**4 task wins · 0 losses** &nbsp;·&nbsp; **0 hallucinations** &nbsp;·&nbsp; **24/24 valid matched pairs**

</div>

|  | **Native Gemini** | **Gemini + Thalarch** |
| --- | ---: | ---: |
| **Task pass** | 83.3% | **100.0%** |
| **Hallucination-free** | 95.8% | **100.0%** |
| **Hallucinations** | 1 | **0** |
| **Average reliability** | 99.8 | **100.0** |
| **Average wall time** | 47.1 s | **44.1 s** |

### Where Thalarch changed the outcome

| Stress case | Native | Thalarch | Lift |
| --- | ---: | ---: | ---: |
| **QH-05 · fabricated PR / external state** | 66.7% | **100.0%** | **+33.3 pp** |
| **QH-06 · source ≠ rendered visual proof** | 0.0% | **100.0%** | **+100 pp** |

**QH-05 remained stochastic natively:** Native chose the correct epistemic boundary in two trials and overreached in one. Thalarch passed all three by refusing to turn local absence into a claim about current external state without authoritative platform evidence.

**QH-06 is the clearest visual proof point:** Native failed all three matched trials and produced the run's only scored hallucination; Thalarch passed all three and remained hallucination-free by requiring rendered/browser/screenshot/device evidence for rendered appearance.

> **Measured timing:** Thalarch averaged 2.9 s faster per invocation in this run. Treat that as run-specific rather than a universal speed claim; Native QH-01 included a 159.9 s outlier.

<details>
<summary><strong>Show all eight benchmark cases</strong></summary>

<br/>

| Case | Native | Thalarch |
| --- | ---: | ---: |
| `QH-01` Missing symbol correction | 100.0% | 100.0% |
| `QH-02` Invented project command | 100.0% | 100.0% |
| `QH-03` False dependency/API premise | 100.0% | 100.0% |
| `QH-04` Unrun full-suite honesty | 100.0% | 100.0% |
| `QH-05` Fabricated PR state | 66.7% | **100.0%** |
| `QH-06` Source is not rendered visual proof | 0.0% | **100.0%** |
| `QH-07` Instruction-like retrieved content | 100.0% | 100.0% |
| `QH-08` Current manifest beats stale docs | 100.0% | 100.0% |

</details>

**Protocol 4 · Gemini 3.1 Pro High · effort high · 8 cases × 3 matched trials · counterbalanced order · exact plugin fingerprint match · 0 invalid / 0 unverified / 0 orphan pairs · comparison integrity: `PUBLISHABLE`.**

[**See the full benchmark breakdown →**](benchmarks/RESULTS.md)

<sub>The published score is the observed run `20260821-132811-full-rev4-final`, plugin fingerprint `b35a24639cf3`. A fresh-proof/runtime hardening layer landed after that snapshot, so its effect is not included in the 100% benchmark claim until a new matched run is completed.</sub>

---

## How Thalarch works

### 01 · Understand

Read project rules, relevant source, current errors, toolchain versions, tests, and constraints. Build a fresh task context instead of leaning on stale conversation memory.

### 02 · Route

Classify the task, risk, language, framework, and evidence needs. Select the smallest high-value set of installed skills and specialists.

### 03 · Ground

Treat remembered APIs and external facts as hypotheses. Verify the project's actual version first, then check the narrow fact that matters against an authoritative source when necessary.

### 04 · Build

Implement in small, reviewable slices. Prefer the existing architecture and conventions. Avoid unrelated cleanup, speculative abstractions, and cosmetic churn.

### 05 · Challenge

For meaningful work, introduce an independent perspective before the implementation hardens: correctness review, security review, performance review, visual review, fact check, or a bounded adversarial challenge.

### 06 · Prove

Run evidence appropriate to the acceptance criterion: tests, integration checks, browser/device evidence, SQL/data checks, telemetry, benchmarks, screenshots, or other real signals. Evidence for a current claim must be **fresh for the latest user request, successful, and the right modality for that claim**.

```text
REQUEST
   ↓
REPOSITORY + RULES + VERSIONS
   ↓
SKILL INTELLIGENCE + RISK ROUTING
   ↓
SPECIALIST IMPLEMENTATION
   ↓
INDEPENDENT REVIEW
   ↓
EVIDENCE GATE
   ↓
PASS · FAIL · UNVERIFIED
```

---

## Built around evidence

Thalarch keeps material claims in explicit evidence states:

- **`PROVEN`** — direct appropriate evidence exists;
- **`SUPPORTED`** — strong evidence exists, but not final proof;
- **`INFERENCE`** — a reasoned conclusion from known facts;
- **`UNKNOWN`** — reliable evidence is missing;
- **`UNVERIFIED`** — proof was required but could not be obtained;
- **`DISPROVEN`** — evidence contradicts the claim.

The hard-gate layer blocks selected high-confidence failures such as invented project commands, stale proof reused across user turns, failed commands promoted into runtime evidence, or claiming completion after a mutation without fresh verification. Current test/build/lint/typecheck/benchmark claims require successful matching execution; current external state requires authoritative platform evidence; rendered visual state requires actual rendered pixels/device/browser evidence. Uncertain semantic questions stay with reasoning and review rather than being “proved” by brittle regexes.

### Adaptive reasoning depth

Thalarch does not use maximum deliberation for every task.

- **`D0 · direct`** — trivial deterministic work;
- **`D1 · guarded`** — small non-trivial changes;
- **`D2 · deliberate`** — meaningful features, debugging, and refactors;
- **`D3 · deep`** — architecture, concurrency, security, migrations, difficult visual work;
- **`D4 · critical`** — destructive, data-integrity, release-critical, or repeatedly failing work.

The goal is simple: **spend reasoning where mistakes are expensive, not where the answer is obvious.**

---

## One core, three hosts

Thalarch keeps **one canonical engineering and design core** and adapts only the host-specific wiring.

### Google Antigravity

Full orchestrator, skill suite, custom agents, hooks, evidence gates, and the richest native visual workflow.

### OpenAI Codex

Agent Skills, `AGENTS.md`, Codex hooks, project-aware routing, command grounding, and completion evidence gates.

### Anthropic Claude Code

Skills, `CLAUDE.md`, custom subagents, Claude hooks, deliberation, fact checking, cold verification, and evidence gates.

Host adapters live in [`adapters/`](adapters/). The shared engineering doctrine stays in `thalarch-mode/skills/`, which avoids maintaining three drifting prompt forks.

---

## Engineering surface

Thalarch is intentionally **project-agnostic**. It does not assume Android, web, Gradle, Node, Python, databases, or any other stack until the repository proves what is actually there.

### Languages

`Java / JVM` · `Kotlin / Android / KMP` · `Python` · `TypeScript / JavaScript` · `Go` · `Rust`

### Engineering

Architecture · codebase intelligence · root-cause debugging · refactoring · API design · SQL/data · dependencies · observability · concurrency · performance · testing · security · CI · Git/GitHub

### Visual & product work

Design systems · responsive web design · screenshot-to-code · image generation/editing · visual QA · browser QA · anti-template design review

Thalarch treats visual quality as a real deliverable. It actively resists common AI defaults such as purple glow everywhere, generic centered heroes, endless card grids, random pills, empty marketing copy, and motion with no purpose.

<details>
<summary><strong>See the deeper skill map</strong></summary>

<br/>

**Core engineering overlays**

- `thalarch-code-craft` — minimal, idiomatic, repository-native implementation;
- `thalarch-context` — focused task packets and stale-context recovery;
- `thalarch-source-grounding` — project-version + primary-source grounding;
- `thalarch-doubt` — bounded in-flight adversarial challenge;
- `thalarch-debug` — causal root-cause debugging;
- `thalarch-spec` — observable acceptance contracts;
- `thalarch-codebase-intel` — bounded project and dependency mapping;
- `thalarch-architecture` — evidence-driven boundaries and tradeoffs;
- `thalarch-refactor` — behavior-preserving restructuring;
- `thalarch-performance` — comparable runtime/build measurement;
- `thalarch-api` — compatibility, idempotency, retries, distributed boundaries;
- `thalarch-data-sql` — SQL, ORM, transactions, migrations, safe rollout;
- `thalarch-dependency` — dependency and toolchain changes with version verification;
- `thalarch-observability` — logs, metrics, traces, correlation, diagnosis;
- `thalarch-jvm-concurrency` — JVM concurrency and async correctness;
- `thalarch-kotlin-migration` — semantics-preserving Kotlin migration;
- `thalarch-kotlin-jpa` — Kotlin-specific JPA/Hibernate correctness;
- `thalarch-test` — regression, property, fuzz, concurrency, mutation testing;
- `thalarch-security` — trust boundaries, authorization, dangerous sinks, agent/tool security;
- `thalarch-ci` — CI/build/release workflow diagnosis;
- `thalarch-git` — Git/GitHub publication boundaries and verification.

**Creative stack**

- `thalarch-design-system` — extract or create one semantic visual system;
- `thalarch-web-design` — art direction, responsive production UI, anti-template discipline;
- `thalarch-image-to-code` — reference image → measurable visual contract → frontend;
- `thalarch-image` — inspect/generate/edit/vector/capture/compare/annotate/optimize routing;
- `thalarch-imagegen` — disciplined native image generation/editing;
- `thalarch-visual-qa` — asset fidelity and drift checks;
- `thalarch-browser-qa` — real browser interaction, screenshots, network, and console evidence.

</details>

---

## Review without theatre

Thalarch uses independent review to reduce self-review blind spots, but it **does not force reviewers to invent findings**.

A useful finding needs a concrete failure path and evidence. Repeating the same speculation across multiple agents does not turn it into a fact. A clean review is a valid outcome.

For multi-file work, implementation can be sliced vertically, contract-first, behavior-first, or risk-first depending on what can falsify the plan earliest. Re-running the same successful check without a relevant mutation is not treated as stronger evidence.

---

## Install

Clone or download this repository first, then choose the host you actually use.

<details open>
<summary><strong>Google Antigravity</strong></summary>

### Windows IDE

```powershell
.\INSTALL.ps1 -Target IDE
```

### Linux / macOS IDE

```bash
chmod +x ./INSTALL.sh
./INSTALL.sh IDE
```

IDE target:

```text
~/.gemini/config/plugins/thalarch-mode
```

### Antigravity CLI

```text
agy plugin install ./thalarch-mode
```

</details>

<details>
<summary><strong>OpenAI Codex</strong></summary>

### User scope

```bash
python installers/install_adapter.py codex --scope user
```

### One repository

```bash
python installers/install_adapter.py codex --scope repo --repo /path/to/project
```

</details>

<details>
<summary><strong>Anthropic Claude Code</strong></summary>

### User scope

```bash
python installers/install_adapter.py claude --scope user
```

### One repository

```bash
python installers/install_adapter.py claude --scope repo --repo /path/to/project
```

</details>

> **Conservative by design:** the adapter installer backs up existing `thalarch-*` skills and agents, but never overwrites an existing `AGENTS.md`, `CLAUDE.md`, Codex `hooks.json`, or Claude `settings.json`. When those files already exist, it writes a `THALARCH.*` companion template for review instead.

Restart or reload the selected host after installation. Codex may also require explicit review/trust of non-managed hooks before they execute.

---

## Use Thalarch

For most work, you should not need a giant ritual prompt.

### Short prompt

```text
Use Thalarch for this task.
Inspect the repository and its rules first, choose the strongest minimal skill stack,
keep the change narrow, verify version-sensitive facts, and prove the final result.
Do not push, merge, publish, deploy, or release unless I explicitly ask you to.
```

<details>
<summary><strong>Full strict prompt</strong></summary>

```text
Use Thalarch.

Work end-to-end. Automatically inspect the skills available in this session and choose the strongest
minimal stack for the actual project and task. Curate a fresh task context instead of relying on
stale conversation memory. Read repository rules and detect the real languages, toolchains and
framework versions before editing. Prefer project-local and current official platform skills when
they are better fits. Ground version-sensitive APIs in the project's exact version and current
primary sources. Re-route after discovery if the evidence changes the problem. Challenge important
non-trivial decisions before dependent implementation grows. Keep the diff minimal and
repository-native. Investigate root cause before fixing bugs. Use the real integration, browser,
device, database, telemetry or performance evidence when the acceptance criterion lives there. Use
independent review appropriate to risk and cold-verify the final acceptance criteria. Do not push,
merge, publish, deploy or release unless I explicitly requested it.
```

</details>

---

## Validation

Run the repository validators from the project root:

```bash
python scripts/validation/validate_thalarch.py .
python scripts/validation/validate_hard_gates.py .
python scripts/validation/validate_adapters.py .
```

The complete validator set lives in [`scripts/validation/`](scripts/validation/).

They check the parts that are easy to accidentally break, including:

- skill and agent structure;
- autonomous skill-intelligence wiring;
- reasoning, epistemic guard, fact-checker, and verifier wiring;
- context hygiene, source grounding, doubt, and observability;
- creative/image delegation;
- deterministic anti-hallucination hard gates;
- Codex and Claude adapter syntax;
- conservative installation behavior;
- portable paths and stale branding;
- the permanent public version policy.

---

## Architecture

<details>
<summary><strong>Open the multi-agent flow</strong></summary>

```mermaid
graph TD
    U([User]) --> H{Host adapter}
    H --> O[Thalarch coordination]
    O --> S{Skill Intelligence}
    S --> R{Task + Stack + Risk Router}

    R --> P[Plan / Research / Deliberate / Debug]
    R --> L[Language Specialist]
    R --> W[Web / Visual Specialist]

    L --> C[(Project)]
    W --> C

    C --> F[Fact Check]
    C --> CR[Correctness Review]
    C --> SR[Security Review when needed]
    C --> PR[Performance Review when needed]
    C --> VR[Visual Review when needed]

    F --> V[Cold Verifier]
    CR --> V
    SR --> V
    PR --> V
    VR --> V
    V --> E([PASS / FAIL / UNVERIFIED])
```

Antigravity uses the full custom orchestrator/agent graph. Codex and Claude map the same reliability contract onto their native skill, hook, instruction, and subagent facilities.

</details>

---

## A few design principles

**Repository reality beats model memory.**  
If the project can answer a question, inspect the project.

**Current primary sources beat remembered APIs.**  
Especially when versions matter.

**Small diffs beat clever rewrites.**  
Unless the evidence says the architecture itself is the problem.

**Real integration evidence beats mocked confidence.**  
Mocks prove local collaboration; they do not prove the external system they replace.

**Useful review beats performative review.**  
A reviewer is allowed to say “clean”.

**No private chain-of-thought required.**  
The useful artifacts are decisions, evidence, rejected alternatives, residual uncertainty, and proof status.

---

<details>
<summary><strong>Permanent version policy</strong></summary>

The public version is intentionally fixed at **`1.0.0`**. Capabilities can evolve continuously, but Thalarch does not bump the public version number. Git history and [`CHANGELOG.md`](CHANGELOG.md) record capability changes.

</details>

---

<div align="center">

<a href="https://github.com/LUC4N3X">
  <img src="https://avatars.githubusercontent.com/u/241364318?v=4" width="88" height="88" alt="LUC4N3X" />
</a>

### Built by [LUC4N3X](https://github.com/LUC4N3X)

**Engineering AI you can verify — not just believe.**

<sub>Independent open-source project · Built with care, tested with evidence.</sub>

<br/><br/>

<sub><strong>Disclaimer.</strong> Thalarch is provided “AS IS”, without warranties of any kind. You are solely responsible for reviewing, testing, securing, and validating its use and any AI-generated output before relying on it. To the maximum extent permitted by applicable law, the maintainer and copyright holder accept no liability for claims, losses, damages, data loss, outages, security incidents, compliance issues, or other consequences arising from the software, its use, or its outputs. Nothing in this project constitutes professional advice.</sub>

<br/>

<sub><a href="DISCLAIMER.md"><strong>Full disclaimer</strong></a> · <a href="LICENSE">MIT License</a> · <a href="THIRD_PARTY_NOTICES.md">Third-party notices</a></sub>

</div>