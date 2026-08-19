# Thalarch for OpenAI Codex

The Codex adapter reuses the canonical Thalarch skills from `thalarch-mode/skills/` instead of maintaining a second prompt fork.

## Native mapping

- Thalarch skills → Codex Agent Skills under `.agents/skills/` or `~/.agents/skills/`.
- Persistent reliability rules → repository/global `AGENTS.md`.
- Independent deep reasoning → native custom agents under `.codex/agents/` or `~/.codex/agents/`.
- Deterministic anti-hallucination enforcement → Codex `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `SubagentStop`, and `Stop` hooks.
- Parallel investigation → Codex's native subagent/worktree facilities when useful.

The installer provides three read-only native Codex agents:

- `thalarch_deliberator` — clean-context challenge/adjudication for difficult decisions;
- `thalarch_fact_checker` — exact material-claim verification;
- `thalarch_verifier` — cold acceptance verification after implementation.

They use Codex's native standalone TOML agent format with `sandbox_mode = "read-only"` and high reasoning effort, while leaving the actual model unpinned so the host/account can resolve an available compatible model.

The hook layer grounds selected project commands and requires verification evidence that is **successful and newer than the final observed mutation**. Codex documents that `PostToolUse` also fires after non-zero Bash exits, so Thalarch does not treat the mere presence of a verification command as success: the hook requires the `tool_response` to provide an explicit success signal. A later failed or unproven verification attempt invalidates earlier success for completion purposes.

The hook does not claim that regex inspection proves arbitrary program correctness; semantic claims still flow through Thalarch reasoning, independent review/fact checking, and cold verification.

## Visual parity

Codex receives the same canonical visual doctrine as Antigravity. In particular, `thalarch-design-system` carries the `VoltAgent/awesome-design-md` reference-atlas protocol and the image/web skills consume the same compact design-capsule approach. User/project identity always wins; one primary reference (optionally one secondary) is used for principles, not cloning.

This does **not** imply every Codex environment exposes raster image generation. Thalarch first inspects host capabilities and uses the atlas for design reasoning, image-to-code, deterministic assets, or raster generation only when the corresponding tool actually exists.

The same runtime proof seal also applies: a test/build/runtime proposition that was not executed or otherwise observed stays `UNVERIFIED`, even when source inspection looks convincing.

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
