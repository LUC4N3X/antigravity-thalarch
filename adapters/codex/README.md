# Thalarch for OpenAI Codex

The Codex adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/`.

## Native mapping

- Thalarch skills → Codex agent skills under `.agents/skills/` or `~/.agents/skills/`.
- Thalarch persistent reliability rules → `AGENTS.md`.
- Deterministic anti-hallucination enforcement → Codex `PreToolUse`, `UserPromptSubmit` and `Stop` hooks.
- Parallel/independent reasoning → Codex subagents/worktrees when available.

## Install

From the Thalarch repository:

```bash
python installers/install_adapter.py codex --scope user
```

For one repository only:

```bash
python installers/install_adapter.py codex --scope repo --repo /path/to/project
```

The installer never overwrites an existing `AGENTS.md`. It installs a `THALARCH.codex.md` companion file and prints a small block you may merge into your own project instructions.

Codex may require hook review/trust before non-managed hooks execute. Inspect them before trusting them.

Thalarch remains version `1.0.0`.