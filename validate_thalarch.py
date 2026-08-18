#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []
plugin = root / "thalarch-mode"

plugin_json = plugin / "plugin.json"
if not plugin_json.exists():
    errors.append("missing thalarch-mode/plugin.json")
else:
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        if data.get("name") != "thalarch-mode":
            errors.append("plugin.json name must be 'thalarch-mode'")
    except Exception as exc:
        errors.append(f"invalid plugin.json: {exc}")

skill_files = sorted((plugin / "skills").glob("*/SKILL.md"))
for skill_md in skill_files:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        errors.append(f"{skill_md.relative_to(root)}: invalid frontmatter")
        continue
    name_m = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
    if not name_m:
        errors.append(f"{skill_md.relative_to(root)}: missing name")
    elif name_m.group(1).strip() != skill_md.parent.name:
        errors.append(f"{skill_md.relative_to(root)}: name does not match folder")
    fm_lines = m.group(1).splitlines()
    for idx, line in enumerate(fm_lines):
        if line == "description: >":
            for continuation in fm_lines[idx + 1:]:
                if continuation and not continuation.startswith("  "):
                    errors.append(f"{skill_md.relative_to(root)}: description continuation must be indented")
                    break
            break

agent_files = sorted((plugin / "agents").glob("*/agent.md"))
for agent_md in agent_files:
    text = agent_md.read_text(encoding="utf-8")
    for key in ["name:", "description:", "tools:", "model:"]:
        if key not in text:
            errors.append(f"{agent_md.relative_to(root)}: missing {key}")

# Structural visual-safety checks.
visual_director = plugin / "agents" / "thalarch-visual-director" / "agent.md"
orchestrator = plugin / "agents" / "thalarch-orchestrator" / "agent.md"
if visual_director.exists():
    if "  - generate_image" not in visual_director.read_text(encoding="utf-8"):
        errors.append("thalarch-visual-director must have generate_image access")
else:
    errors.append("missing thalarch-visual-director")

if orchestrator.exists() and "  - generate_image" in orchestrator.read_text(encoding="utf-8"):
    errors.append("thalarch-orchestrator must not have direct generate_image access")

# Structural polyglot checks introduced in 2.2.
language_agents = {
    "java": "thalarch-java-engineer",
    "kotlin": "thalarch-kotlin-engineer",
    "python": "thalarch-python-engineer",
    "typescript": "thalarch-typescript-engineer",
    "go": "thalarch-go-engineer",
    "rust": "thalarch-rust-engineer",
}
for language, agent_name in language_agents.items():
    skill_path = plugin / "skills" / f"thalarch-{language}" / "SKILL.md"
    agent_path = plugin / "agents" / agent_name / "agent.md"
    if not skill_path.exists():
        errors.append(f"missing polyglot skill: {skill_path.relative_to(root)}")
    if not agent_path.exists():
        errors.append(f"missing polyglot agent: {agent_path.relative_to(root)}")
        continue
    agent_text = agent_path.read_text(encoding="utf-8")
    if "skills/thalarch-code-craft" not in agent_text:
        errors.append(f"{agent_path.relative_to(root)} must include thalarch-code-craft")
    if f"skills/thalarch-{language}" not in agent_text:
        errors.append(f"{agent_path.relative_to(root)} must include thalarch-{language}")

for p in root.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(root)
    if "__pycache__" in p.parts or p.suffix == ".pyc":
        errors.append(f"generated Python cache must not be distributed: {rel}")
        continue
    if p.resolve() == Path(__file__).resolve():
        continue
    if p.suffix.lower() not in {".md", ".json", ".py", ".ps1", ".sh", ".txt", ".yml", ".yaml"}:
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    lowered = text.lower()
    if "apex mode" in lowered or "apex-" in lowered:
        errors.append(f"stale pre-Thalarch branding in {rel}")
    if re.search(r"(?i)c:\\users\\[^\\\s]+", text):
        errors.append(f"absolute Windows user path in {rel}")
    if re.search(r"/(?:home|users)/[^/\s]+/", text):
        errors.append(f"absolute Unix/macOS user path in {rel}")

required = [
    root / "README.md",
    root / "LICENSE",
    root / "INSTALL.ps1",
    root / "INSTALL.sh",
    root / "TEST-PROMPTS.md",
    plugin / "hooks.json",
    plugin / "skills" / "thalarch-code-craft" / "SKILL.md",
    plugin / "skills" / "thalarch-refactor" / "SKILL.md",
    plugin / "skills" / "thalarch-performance" / "SKILL.md",
    plugin / "skills" / "thalarch-api" / "SKILL.md",
    plugin / "skills" / "thalarch-data-sql" / "SKILL.md",
    plugin / "skills" / "thalarch-dependency" / "SKILL.md",
    plugin / "skills" / "thalarch-design-system" / "SKILL.md",
    plugin / "skills" / "thalarch-web-design" / "SKILL.md",
    plugin / "skills" / "thalarch-image" / "SKILL.md",
    plugin / "skills" / "thalarch-imagegen" / "SKILL.md",
    plugin / "skills" / "thalarch-visual-qa" / "SKILL.md",
    plugin / "skills" / "thalarch-visual-qa" / "scripts" / "image_probe.py",
    plugin / "skills" / "thalarch-visual-qa" / "scripts" / "image_compare.py",
    plugin / "agents" / "thalarch-web-designer" / "agent.md",
    plugin / "agents" / "thalarch-design-reviewer" / "agent.md",
    plugin / "agents" / "thalarch-vision-reviewer" / "agent.md",
]
for p in required:
    if not p.exists():
        errors.append(f"missing required file: {p.relative_to(root)}")

if errors:
    print("THALARCH VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH VALIDATION PASSED")
print("skills:", len(skill_files))
print("agents:", len(agent_files))
print("hooks:", (plugin / "hooks.json").exists())
print("visual_director_generate_image: enforced")
print("orchestrator_generate_image: structurally delegated")
print("polyglot_specialists:", ", ".join(language_agents))
print("portable-path check: passed")
