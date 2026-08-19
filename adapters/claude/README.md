# Thalarch for Claude Code

The Claude Code adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/` instead of maintaining a Claude-specific fork of the engineering doctrine.

## Native mapping

- Thalarch skills → `.claude/skills/` or `~/.claude/skills/`.
- Persistent reliability rules → project/user `CLAUDE.md`.
- Independent deliberation, exact fact checking, and cold verification → custom Claude subagents.
- Deterministic anti-hallucination enforcement → Claude Code `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SubagentStop`, and `Stop` hooks.

The adapter installs three read-only specialist definitions:

- `thalarch-deliberator` — clean-context challenge/adjudication for hard decisions;
- `thalarch-fact-checker` — exact claim verification;
- `thalarch-verifier` — cold acceptance verification after implementation.

The Stop gate requires project-native verification that is **successful and newer than the final observed mutation**. Claude Code exposes successful and failed tool execution as separate lifecycle events, so a later failed verification attempt invalidates an earlier successful check for completion purposes. If a required proof cannot be obtained, an explicit `UNVERIFIED` result is preferred over fabricated completion.

## Install

```bash
python installers/install_adapter.py claude --scope user
```

For one repository only:

```bash
python installers/install_adapter.py claude --scope repo --repo /path/to/project
```

If no `CLAUDE.md` exists at the target scope, the installer creates the Thalarch instruction file in the native location. If one already exists, it is preserved and `THALARCH.claude.md` is written beside it for review/merge.

An existing Claude `settings.json` is also preserved. Thalarch writes `THALARCH.settings.json` beside it; when no settings file exists, the installer writes the active hook configuration with an absolute interpreter/script path.

Thalarch remains version `1.0.0`.