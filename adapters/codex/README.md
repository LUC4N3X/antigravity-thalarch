# Thalarch for OpenAI Codex

The Codex adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/` instead of maintaining a second prompt fork.

## Native mapping

- Thalarch skills → Codex Agent Skills under `.agents/skills/` or `~/.agents/skills/`.
- Persistent reliability rules → repository/global `AGENTS.md`.
- Deterministic anti-hallucination enforcement → Codex `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `SubagentStop`, and `Stop` hooks.
- Independent/parallel investigation → Codex's native subagent/worktree facilities when the current environment exposes them.

The hook layer grounds selected project commands and requires fresh verification evidence **after the final observed mutation**. It does not claim that regex inspection proves arbitrary program correctness; semantic claims still flow through Thalarch reasoning, review, and verification.

## Install

From the Thalarch repository:

```bash
python installers/install_adapter.py codex --scope user
```

For one repository only:

```bash
python installers/install_adapter.py codex --scope repo --repo /path/to/project
```

If no relevant `AGENTS.md` exists, the installer creates the Thalarch instruction file in the native location. If one already exists, it is preserved and `THALARCH.codex.md` is written beside it for review/merge.

Likewise, an existing Codex `hooks.json` is never overwritten. Thalarch writes `THALARCH.hooks.json` beside it so the user can review and merge the hook group. When no hook config exists, the installer writes an active native `hooks.json` with an absolute interpreter/script path.

Codex requires review/trust for non-managed command hooks before they execute; use the host's hook-review UI/command rather than bypassing that safety casually.

Thalarch remains version `1.0.0`.