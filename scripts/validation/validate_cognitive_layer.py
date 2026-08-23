#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []
skills = root / "thalarch-mode" / "skills"

required_skills = [
    "thalarch-memory",
    "thalarch-experience",
    "thalarch-project-brain",
    "thalarch-teacher",
]

for name in required_skills:
    path = skills / name / "SKILL.md"
    if not path.is_file():
        errors.append(f"missing cognitive skill: {path.relative_to(root)}")
        continue
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{path.relative_to(root)}: missing frontmatter")
    if not re.search(rf"(?m)^name:\s*{re.escape(name)}\s*$", text):
        errors.append(f"{path.relative_to(root)}: name/frontmatter mismatch")

checks = {
    skills / "thalarch-memory" / "SKILL.md": [
        "IGNORE",
        "SESSION",
        "PROJECT",
        "GENERAL",
        "current repository/runtime evidence wins",
        "private chain-of-thought",
        "scripts/memory_store.py",
        "MEMORY USED",
        "MEMORY REJECTED",
    ],
    skills / "thalarch-experience" / "SKILL.md": [
        "Experience card",
        "DISCRIMINATOR",
        "FAILED_ALTERNATIVES",
        "COUNTEREXAMPLE",
        "SESSION → PROJECT → GENERAL",
        "One impressive anecdote is not enough",
    ],
    skills / "thalarch-project-brain" / "SKILL.md": [
        ".thalarch/brain/",
        "regressions.md",
        "Current truth wins",
        "Last verified",
        "requires user/project authorization",
    ],
    skills / "thalarch-teacher" / "SKILL.md": [
        "student candidate → independent judgment",
        "Hard gates before scores",
        "PASS",
        "REVISE",
        "FAIL",
        "UNVERIFIED",
        "two targeted revision cycles",
        "Anti-grader-hacking",
        "thalarch-autoresearch",
        "holdout",
    ],
    skills / "thalarch-compound" / "SKILL.md": [
        "thalarch-experience",
        "thalarch-memory",
        "thalarch-project-brain",
        "IGNORE",
        "SESSION",
        "PROJECT",
        "GENERAL",
    ],
    skills / "thalarch-context" / "SKILL.md": [
        "thalarch-memory",
        "MEMORY USED",
        "MEMORY REJECTED",
        "load the entire Project Brain",
    ],
    skills / "thalarch-router" / "SKILL.md": [
        "## Cognitive routing",
        "thalarch-memory",
        "thalarch-experience",
        "thalarch-project-brain",
        "thalarch-teacher",
        "thalarch-autoresearch",
    ],
}

for path, terms in checks.items():
    if not path.is_file():
        errors.append(f"missing cognitive wiring file: {path.relative_to(root)}")
        continue
    text = path.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            errors.append(f"{path.relative_to(root)} missing cognitive guard: {term}")

memory_script = skills / "thalarch-memory" / "scripts" / "memory_store.py"
if not memory_script.is_file():
    errors.append(f"missing memory store helper: {memory_script.relative_to(root)}")
else:
    try:
        py_compile.compile(str(memory_script), doraise=True)
    except Exception as exc:
        errors.append(f"memory store helper does not compile: {exc}")

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "memory.sqlite3"

        def run(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(memory_script), "--db", str(db), *args],
                text=True,
                capture_output=True,
                check=False,
            )

        init = run("init")
        if init.returncode != 0:
            errors.append(f"memory store init smoke failed: {init.stderr.strip()}")

        add_project = run(
            "add",
            "--scope", "PROJECT",
            "--project", "demo",
            "--kind", "regression",
            "--title", "Media identity must stay stable",
            "--body", "Queue operations must preserve stable media identity.",
            "--trigger", "queue removal or reorder",
            "--tags", "media,queue,identity",
            "--evidence", "PROVEN",
            "--source", "test:queue-identity",
            "--confidence", "0.9",
        )
        if add_project.returncode != 0:
            errors.append(f"memory store project add smoke failed: {add_project.stderr.strip()}")

        add_general_without_gate = run(
            "add",
            "--scope", "GENERAL",
            "--kind", "diagnostic",
            "--title", "Bad universal",
            "--body", "One task should not become general automatically.",
            "--evidence", "PROVEN",
        )
        if add_general_without_gate.returncode == 0:
            errors.append("GENERAL memory insertion must require explicit --generalizable")

        search = run("search", "--query", "queue identity", "--project", "demo", "--limit", "5")
        if search.returncode != 0:
            errors.append(f"memory store search smoke failed: {search.stderr.strip()}")
        else:
            try:
                payload = json.loads(search.stdout)
                if not payload or payload[0].get("title") != "Media identity must stay stable":
                    errors.append("memory store search did not retrieve the expected project memory")
            except Exception as exc:
                errors.append(f"memory store search did not emit valid JSON: {exc}")

        if add_project.returncode == 0:
            try:
                memory_id = json.loads(add_project.stdout)["id"]
            except Exception as exc:
                errors.append(f"memory store add did not emit an id: {exc}")
            else:
                retire = run("retire", "--id", memory_id)
                if retire.returncode != 0:
                    errors.append(f"memory store retire smoke failed: {retire.stderr.strip()}")

cognitive_cases = root / "benchmarks" / "cognitive-cases.json"
if not cognitive_cases.is_file():
    errors.append("missing benchmarks/cognitive-cases.json")
else:
    try:
        cases = json.loads(cognitive_cases.read_text(encoding="utf-8"))
        ids = [case.get("id") for case in cases]
        if len(cases) < 8:
            errors.append("cognitive benchmark set must contain at least 8 cases")
        if len(ids) != len(set(ids)):
            errors.append("cognitive benchmark case ids must be unique")
        required_categories = {"memory-freshness", "generalization", "privacy", "teacher-hard-gate", "eval-gaming"}
        categories = {case.get("category") for case in cases}
        missing = required_categories - categories
        if missing:
            errors.append(f"cognitive benchmark missing categories: {', '.join(sorted(missing))}")
    except Exception as exc:
        errors.append(f"invalid cognitive benchmark JSON: {exc}")

for path in [
    root / "docs" / "COGNITIVE-LAYER.md",
    root / "docs" / "COGNITIVE-TEST-PROMPTS.md",
]:
    if not path.is_file():
        errors.append(f"missing cognitive documentation: {path.relative_to(root)}")

if errors:
    print("THALARCH COGNITIVE LAYER VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH COGNITIVE LAYER VALIDATION PASSED")
print("skills:", ", ".join(required_skills))
print("memory_store_smoke: passed")
print("memory_authority: current_evidence_over_memory")
print("generalization_gate: enforced")
print("project_brain: opt_in")
print("teacher_hard_gates: enforced")
print("teacher_revision_loop: bounded")
print("grader_hacking: rejected")
print("cognitive_cases: validated")
