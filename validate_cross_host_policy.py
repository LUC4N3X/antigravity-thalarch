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
    root / "thalarch-mode/hooks/pre_invocation_epistemic_guard.py": [
        "requires execution/runtime/CI/device/browser evidence",
        "keep the proposition UNVERIFIED",
        "never use PROVEN/SUPPORTED",
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
        "remain `UNVERIFIED`",
    ],
    root / "adapters/claude/CLAUDE.md": [
        "Visual/design reference contract",
        "VoltAgent/awesome-design-md",
        "remains `UNVERIFIED`",
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
    # Keep raw source too for identifiers/comments, but use AST-folded constants so
    # adjacent literals split across formatting lines are checked as Python sees them.
    return source + "\n" + "\n".join(strings)


for path, terms in checks.items():
    if not path.is_file():
        errors.append(f"missing cross-host policy file: {path.relative_to(root)}")
        continue
    text = policy_text(path)
    for term in terms:
        if term not in text:
            errors.append(f"{path.relative_to(root)} missing policy guard: {term}")

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
print("design_reference_atlas: awesome-design-md")
print("visual_policy: canonical_cross_host")
print("python_policy_strings: ast_semantic")
