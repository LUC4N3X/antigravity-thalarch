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

for skill_md in sorted((plugin / "skills").glob("*/SKILL.md")):
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

for agent_md in sorted((plugin / "agents").glob("*/agent.md")):
    text = agent_md.read_text(encoding="utf-8")
    for key in ["name:", "description:", "tools:", "model:"]:
        if key not in text:
            errors.append(f"{agent_md.relative_to(root)}: missing {key}")

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
print("skills:", len(list((plugin / "skills").glob("*/SKILL.md"))))
print("agents:", len(list((plugin / "agents").glob("*/agent.md"))))
print("hooks:", (plugin / "hooks.json").exists())
print("portable-path check: passed")
