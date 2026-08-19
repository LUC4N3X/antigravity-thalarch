# Thalarch adapters

Thalarch keeps one canonical capability core in `thalarch-mode/skills/` and exposes it through thin host adapters.

Supported hosts:

- Google Antigravity — native plugin, skills, custom agents and hard evidence gates in `thalarch-mode/`.
- OpenAI Codex — Agent Skills, `AGENTS.md`, native custom deliberation/fact-check/verifier agents and Codex lifecycle hooks.
- Anthropic Claude Code — skills, `CLAUDE.md`, native non-editing custom subagents and Claude lifecycle hooks.

## Design rule

Do not fork the engineering logic per model. Shared reasoning, epistemic, language, testing, review, security, design and visual skills stay canonical. Adapters translate discovery paths, tool names, subagent configuration and lifecycle-hook schemas only.

Specialist isolation follows host reality rather than marketing labels. A verifier may need shell execution to run project-native tests/builds, so “non-editing” means it must not intentionally change source/config/external state; ordinary generated build/cache artifacts are allowed only as a consequence of verification under the user's host permissions.

All host completion gates follow the same evidence invariant: verification must be both **successful and newer than the final relevant mutation**. A later failed verification invalidates earlier success. When proof cannot be obtained, `UNVERIFIED` is a valid outcome; fabricated PASS is not.

This keeps behavior comparable across models and makes cross-model evaluation meaningful.

The public Thalarch version remains `1.0.0` on every host.