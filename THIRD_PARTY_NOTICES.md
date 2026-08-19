# Third-Party Notices

This document records third-party license obligations and provenance for material incorporated into
Thalarch. It is intentionally separate from the product README so compatibility and product identity
remain distinct from legal attribution.

The repository-level MIT license applies to Thalarch-authored material except where a file or portion
is identified here under another license. Attribution does not imply affiliation, sponsorship,
endorsement, or authorship of Thalarch by an upstream project or maintainer.

## Licensed material

### Kotlin / JetBrains — `Kotlin/kotlin-agent-skills`

- Upstream: https://github.com/Kotlin/kotlin-agent-skills
- License: Apache License 2.0
- License text: [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt)
- No root `NOTICE` file was present in the upstream repository when this record was prepared.

Relevant upstream work:

- `kotlin-tooling-java-to-kotlin`
- `kotlin-backend-jpa-entity-mapping`

Relevant Thalarch files:

- `thalarch-mode/skills/thalarch-kotlin-migration/SKILL.md`
- `thalarch-mode/skills/thalarch-kotlin-jpa/SKILL.md`

These Thalarch files contain material modified from the upstream Apache-2.0 work and are identified as
modified in their file metadata. Their structure, wording, scope, authorization boundaries,
host behavior, evidence requirements, and integration model differ from upstream.

### Addy Osmani — `addyosmani/agent-skills`

- Upstream: https://github.com/addyosmani/agent-skills
- License: MIT
- Copyright: Copyright (c) 2025 Addy Osmani
- License text: [`LICENSES/MIT-Addy-Agent-Skills.txt`](LICENSES/MIT-Addy-Agent-Skills.txt)

Thalarch's reliability workflows incorporate licensed process material and engineering patterns from
this project within a substantially different routing, evidence, authorization, and multi-host
architecture. Relevant areas include source grounding, context hygiene, bounded challenge,
incremental implementation, observability, and browser-evidence workflows.

Primary Thalarch areas:

- `thalarch-mode/skills/thalarch-source-grounding/`
- `thalarch-mode/skills/thalarch-context/`
- `thalarch-mode/skills/thalarch-doubt/`
- related orchestration/evidence material identified in the repository source map.

### Leonxlnx — `taste-skill`

- Upstream: https://github.com/Leonxlnx/taste-skill
- License: MIT
- Copyright: Copyright (c) 2026 Leonxlnx
- License text: [`LICENSES/MIT-Taste-Skill.txt`](LICENSES/MIT-Taste-Skill.txt)

Thalarch's visual-production system incorporates licensed design-process material and patterns from
this project within a different routing, evidence, accessibility, host, and completion model.

Primary Thalarch areas:

- `thalarch-mode/skills/thalarch-web-design/`
- `thalarch-mode/skills/thalarch-image-to-code/`
- related design-system and visual-production guidance identified in the repository source map.

## Reference and discovery sources

The following projects are referenced for research, discovery, comparison, or specialist selection.
They are not presented as bundled dependencies, and their inclusion here does not imply that their
source code or documentation is redistributed by Thalarch:

- `webfuse-com/awesome-autoresearch`
- `supratikpm/gemini-autoresearch`
- `junjunjunbong/research-loop`
- `uditgoenka/autoresearch`
- `sentient-agi/EvoSkill`
- `decebals/claude-code-java`
- `alirezarezvani/claude-skills`
- `VoltAgent/awesome-design-md`
- GitHub Spec Kit / Awesome Copilot and other public engineering references when explicitly cited in
  repository documentation.

The detailed source-selection map lives at:
`thalarch-mode/skills/thalarch-skill-intelligence/references/known-high-value-sources.md`.

A reference to a project, public API, technique, or general engineering principle does not by itself
mean that protectable source text or code is distributed in this repository.

## Trademarks and affiliation

Google, Gemini, Antigravity, OpenAI, Codex, Anthropic, Claude, JetBrains, Kotlin, GitHub, Microsoft,
and other product or project names and marks belong to their respective owners. Names are used only
to describe compatibility, provenance, or technical context. Thalarch is independently maintained
and is not affiliated with, sponsored by, or endorsed by those companies or upstream maintainers
unless explicitly stated by the relevant owner.

## Provenance rule for future contributions

When a contribution reproduces or modifies third-party code, documentation, configuration, or other
protectable material, record the upstream source, copyright notice where provided, license,
modification status, and any required `NOTICE` material before distribution. When only a general
engineering idea is used, express it independently in Thalarch's own structure and language and avoid
reproducing distinctive upstream wording or examples.