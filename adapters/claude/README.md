# Thalarch for Claude Code

The Claude Code adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/` instead of maintaining a Claude-specific fork of the engineering doctrine.

## Native mapping

- Thalarch skills → `.claude/skills/` or `~/.claude/skills/`.
- Persistent reliability rules → project/user `CLAUDE.md`.
- Independent deliberation, exact fact checking, and cold verification → custom Claude subagents.
- Deterministic anti-hallucination enforcement → Claude Code `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SubagentStop`, and `Stop` hooks.

The adapter installs three **non-editing** specialist definitions:

- `thalarch-deliberator` — clean-context challenge/adjudication for hard decisions;
- `thalarch-fact-checker` — exact claim verification;
- `thalarch-verifier` — cold acceptance verification after implementation.

They use `model: inherit` so the adapter works with the model selected by the user's Claude Code environment, `effort: high` for difficult specialist reasoning, and `permissionMode: default` so evidence-gathering Bash commands can execute through the user's normal permission policy. `plan` mode is intentionally not used because Claude Code's plan permission mode cannot execute commands, which would prevent a verifier from running real tests/build checks.

The specialists do not intentionally modify project source/configuration or external state. Verification commands may create ordinary generated build/cache artifacts when permitted by the host; that is evidence production, not permission for source edits.

The Stop gate requires project-native verification that is **successful and newer than the final observed mutation**. Claude Code exposes successful and failed tool execution as separate lifecycle events, so a later failed verification attempt invalidates an earlier successful check for completion purposes. If a required proof cannot be obtained, an explicit `UNVERIFIED` result is preferred over fabricated completion.

## Visual parity

Claude Code receives the same canonical visual doctrine as Antigravity. `thalarch-design-system` includes the `VoltAgent/awesome-design-md` reference-atlas protocol, and the same design capsule is used by web/image workflows: one primary reference by task fit, at most one secondary reference, project/user identity first, and no blind brand cloning.

The actual production medium remains capability-aware. If the current Claude Code environment lacks raster image generation/editing, Thalarch uses the reference for design reasoning, deterministic/vector assets, image-to-code, or implementation guidance instead of pretending an unavailable image tool exists.

The same runtime proof seal is preserved across hosts: execution-dependent propositions remain `UNVERIFIED` until the required run/CI/device/browser evidence is actually observed.

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
