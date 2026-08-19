#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []

checks = {
    root / "thalarch-mode/skills/thalarch-epistemic-guard/SKILL.md": [
        "Runtime proof seal",
        "cannot** be promoted to `PROVEN` or `SUPPORTED`",
        "This seal is host-agnostic",
    ],
    root / "thalarch-mode/skills/thalarch-design-system/SKILL.md": [
        "External design-reference atlas",
        "references/awesome-design-md.md",
        "VoltAgent/awesome-design-md",
    ],
    root / "thalarch-mode/skills/thalarch-design-system/references/awesome-design-md.md": [
        "VoltAgent/awesome-design-md",
        "design-reference atlas",
        "one primary reference",
        "at most one secondary",
    ],
    root / "thalarch-mode/skills/thalarch-imagegen/SKILL.md": [
        "awesome-design-md.md",
        "Design-reference assist",
    ],
    root / "thalarch-mode/agents/thalarch-visual-director/agent.md": [
        "VoltAgent/awesome-design-md",
        "art-direction assistant",
    ],
    root / "adapters/codex/AGENTS.md": [
        "Visual/design reference contract",
        "VoltAgent/awesome-design-md",
        "Verdict seal",
    ],
    root / "adapters/claude/CLAUDE.md": [
        "Visual/design reference contract",
        "VoltAgent/awesome-design-md",
        "Verdict seal",
    ],
    root / "adapters/codex/README.md": [
        "Visual parity",
        "VoltAgent/awesome-design-md",
    ],
    root / "adapters/claude/README.md": [
        "Visual parity",
        "VoltAgent/awesome-design-md",
    ],
}


def policy_text(path: Path) -> str:
    """Return semantic searchable text, including Python's folded string literals."""
    source = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        return source

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        errors.append(f"invalid Python policy file {path.relative_to(root)}: {exc}")
        return source

    strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    return source + "\n" + "\n".join(strings)


def require_terms(path: Path, terms: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing cross-host policy file: {path.relative_to(root)}")
        return ""
    text = policy_text(path)
    for term in terms:
        if term not in text:
            errors.append(f"{path.relative_to(root)} missing policy guard: {term}")
    return text


for path, terms in checks.items():
    require_terms(path, terms)

# The Antigravity hook is executable policy. Validate the semantic cluster instead of brittle prose.
hook = root / "thalarch-mode/hooks/pre_invocation_epistemic_guard.py"
hook_text = require_terms(hook, ["VERDICT SEAL", "UNVERIFIED", "PROVEN", "SUPPORTED"])
hook_lower = hook_text.lower()
for concept in [
    "execution/runtime/ci/device/browser evidence",
    "factual proposition",
    "evidence is unavailable",
    "missing proof",
]:
    if concept not in hook_lower:
        errors.append(f"{hook.relative_to(root)} missing verdict-seal concept: {concept}")

# Codex and Claude must preserve the same proposition-level semantics, not merely mention statuses.
for adapter in [root / "adapters/codex/AGENTS.md", root / "adapters/claude/CLAUDE.md"]:
    if not adapter.is_file():
        continue
    text = adapter.read_text(encoding="utf-8").lower()
    for concept in [
        "factual proposition",
        "execution/runtime/ci/device/browser evidence",
        "unverified",
        "proven",
        "supported",
        "evidence was unavailable",
    ]:
        if concept not in text:
            errors.append(f"{adapter.relative_to(root)} missing cross-host verdict concept: {concept}")

# Permanent public version contract.
for path in [root / "adapters/codex/AGENTS.md", root / "adapters/claude/CLAUDE.md"]:
    if path.is_file() and "Thalarch 1.0.0" not in path.read_text(encoding="utf-8"):
        errors.append(f"{path.relative_to(root)} must preserve public version 1.0.0")

if errors:
    print("THALARCH CROSS-HOST POLICY VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH CROSS-HOST POLICY VALIDATION PASSED")
print("version: 1.0.0 (fixed)")
print("runtime_proof_seal: antigravity_codex_claude")
print("verdict_semantics: proposition_level")
print("design_reference_atlas: awesome-design-md")
print("visual_policy: canonical_cross_host")
print("python_policy_strings: ast_semantic")
