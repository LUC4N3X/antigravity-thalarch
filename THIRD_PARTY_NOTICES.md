# Third-Party Notices

Thalarch contains original work and adaptations informed by permissively licensed open-source projects.
This file records provenance and applicable upstream license terms. The repository-level MIT license
covers Thalarch-authored material except where a file or portion is explicitly identified here under
another license.

Attribution does **not** imply affiliation, sponsorship, endorsement, or authorship of Thalarch by any
upstream project or maintainer.

## Adapted material

### Kotlin / JetBrains — `Kotlin/kotlin-agent-skills`

- Upstream: https://github.com/Kotlin/kotlin-agent-skills
- Upstream license: Apache License 2.0
- License copy: [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt)
- Upstream repository did not contain a root `NOTICE` file when this notice was prepared.

Thalarch includes substantially modified/adapted workflow material based in part on these upstream
skills:

- `kotlin-tooling-java-to-kotlin` → `thalarch-mode/skills/thalarch-kotlin-migration/SKILL.md`
- `kotlin-backend-jpa-entity-mapping` → `thalarch-mode/skills/thalarch-kotlin-jpa/SKILL.md`

The Thalarch versions change structure, wording, scope, authorization boundaries, host behavior,
evidence requirements, and integration with Thalarch's verification model. The upstream Apache-2.0
license and attribution are retained for the adapted material.

### Addy Osmani — `addyosmani/agent-skills`

- Upstream: https://github.com/addyosmani/agent-skills
- Upstream license: MIT
- Copyright: Copyright (c) 2025 Addy Osmani
- License copy: [`LICENSES/MIT-Addy-Agent-Skills.txt`](LICENSES/MIT-Addy-Agent-Skills.txt)

Thalarch's source-grounding/context/doubt reliability workflows were informed by and, in places,
adapted from process mechanics in this project, including source-driven development, context
engineering, bounded doubt/challenge, incremental implementation, observability, and browser-evidence
patterns. The Thalarch files are substantially reorganized and integrated with a different evidence,
routing, authorization, and multi-host model.

Primary affected areas include:

- `thalarch-mode/skills/thalarch-source-grounding/`
- `thalarch-mode/skills/thalarch-context/`
- `thalarch-mode/skills/thalarch-doubt/`
- related orchestration/evidence workflow material where the same mechanics are explicitly documented
  in the repository's source map.

### Leonxlnx — `taste-skill`

- Upstream: https://github.com/Leonxlnx/taste-skill
- Upstream license: MIT
- Copyright: Copyright (c) 2026 Leonxlnx
- License copy: [`LICENSES/MIT-Taste-Skill.txt`](LICENSES/MIT-Taste-Skill.txt)

Thalarch's visual-production workflow was informed by and, in places, adapted from Taste Skill's
brief-inference, anti-template, design-calibration, and image-to-code mechanics. Thalarch changes the
wording, defaults, routing rules, evidence model, host behavior, accessibility constraints, and
completion criteria.

Primary affected areas include:

- `thalarch-mode/skills/thalarch-web-design/`
- `thalarch-mode/skills/thalarch-image-to-code/`
- related design-system and visual-production guidance where provenance is documented in the source map.

## Reference and discovery sources

The following projects are referenced as research, discovery, comparison, or specialist sources.
They are **not** presented as bundled dependencies, and no claim is made that their maintainers
endorse Thalarch:

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

The detailed internal discovery map lives at:
`thalarch-mode/skills/thalarch-skill-intelligence/references/known-high-value-sources.md`.

A reference to a project, technique, public API, or general engineering idea does not by itself mean
that project code or text is redistributed. If future contributions copy or adapt protectable
expression, the contributor must record the source, license, original notice, and modification status
before distribution.

## Trademarks and affiliation

Google, Gemini, Antigravity, OpenAI, Codex, Anthropic, Claude, JetBrains, Kotlin, GitHub, Microsoft,
and other product/project names and marks belong to their respective owners. Names are used here only
to describe compatibility, provenance, or technical context. Thalarch is independently maintained and
is not affiliated with, sponsored by, or endorsed by those companies or upstream maintainers unless
explicitly stated by the relevant owner.

## Contribution provenance rule

New third-party material must not be silently absorbed into Thalarch. When protectable text, code,
configuration, or other material is copied or adapted, record at minimum:

1. upstream repository/file URL;
2. upstream copyright holder/notice where provided;
3. upstream license;
4. whether the material is copied, adapted, or reference-only;
5. a prominent modification notice when the upstream license requires one;
6. any required `NOTICE` material.

When only a general idea or engineering principle is used, rewrite it in Thalarch's own structure and
language and avoid copying distinctive wording or examples.