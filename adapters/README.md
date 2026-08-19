# Thalarch adapters

Thalarch keeps one canonical capability core in `thalarch-mode/skills/` and exposes it through thin host adapters.

Supported hosts:

- Google Antigravity — native plugin, agents and hard gates in `thalarch-mode/`.
- OpenAI Codex — agent skills, `AGENTS.md` guidance and Codex-native hooks.
- Anthropic Claude Code — skills, `CLAUDE.md` guidance, custom subagents and Claude-native hooks.

## Design rule

Do not fork the engineering logic per model. Shared reasoning, epistemic, language, testing, review, security, design and visual skills stay canonical. Adapters translate discovery paths, tool names, subagent configuration and lifecycle-hook schemas only.

This keeps behavior comparable across models and makes cross-model evaluation meaningful.

The public Thalarch version remains `1.0.0` on every host.