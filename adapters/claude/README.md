# Thalarch for Claude Code

The Claude Code adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/`.

## Native mapping

- Thalarch skills → `.claude/skills/` or `~/.claude/skills/`.
- Persistent reliability rules → `CLAUDE.md` companion guidance.
- Independent deliberation/fact checking/verification → custom Claude subagents.
- Deterministic anti-hallucination enforcement → Claude Code `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SubagentStop` and `Stop` hooks.

## Install

```bash
python installers/install_adapter.py claude --scope user
```

For one repository only:

```bash
python installers/install_adapter.py claude --scope repo --repo /path/to/project
```

The installer does not overwrite an existing `CLAUDE.md`; it installs a `THALARCH.claude.md` companion. Claude Code supports project skills, project subagents and project hook settings, so the adapter stays native to Claude rather than emulating Antigravity.

Thalarch remains version `1.0.0`.