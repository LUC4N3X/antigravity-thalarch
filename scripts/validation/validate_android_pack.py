#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []

skills = root / "thalarch-mode" / "skills"
required_skills = [
    "thalarch-android",
    "thalarch-media3",
    "thalarch-compose-ui",
    "thalarch-entity-matching",
    "thalarch-localization",
    "thalarch-no-regression",
]

for name in required_skills:
    path = skills / name / "SKILL.md"
    if not path.is_file():
        errors.append(f"missing Android engineering skill: {path.relative_to(root)}")
        continue
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{path.relative_to(root)}: missing frontmatter")
    if not re.search(rf"(?m)^name:\s*{re.escape(name)}\s*$", text):
        errors.append(f"{path.relative_to(root)}: name/frontmatter mismatch")

references = [
    skills / "thalarch-android" / "references" / "android-performance.md",
    skills / "thalarch-android" / "references" / "room-pagination.md",
    skills / "thalarch-android" / "references" / "deprecation-migration.md",
]
for path in references:
    if not path.is_file():
        errors.append(f"missing Android engineering reference: {path.relative_to(root)}")

android = skills / "thalarch-android" / "SKILL.md"
router = skills / "thalarch-router" / "SKILL.md"

required_wiring = {
    android: [
        "thalarch-media3",
        "thalarch-compose-ui",
        "thalarch-entity-matching",
        "thalarch-localization",
        "thalarch-no-regression",
        "references/android-performance.md",
        "references/room-pagination.md",
        "references/deprecation-migration.md",
        "No-Regression Contract",
    ],
    router: [
        "thalarch-media3",
        "thalarch-compose-ui",
        "thalarch-entity-matching",
        "thalarch-localization",
        "thalarch-no-regression",
        "## Android routing",
    ],
}

for path, terms in required_wiring.items():
    if not path.is_file():
        errors.append(f"missing routing file: {path.relative_to(root)}")
        continue
    text = path.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            errors.append(f"{path.relative_to(root)} missing Android pack wiring: {term}")

performance_ref = references[0]
if performance_ref.is_file():
    text = performance_ref.read_text(encoding="utf-8")
    for term in [
        "Regex",
        "SimpleCache",
        "while (isActive)",
        "Audit first. Mutate second.",
        "native allocations",
        "audio-only playback",
    ]:
        if term not in text:
            errors.append(f"{performance_ref.relative_to(root)} missing hot-path guard: {term}")

paging_ref = references[1]
if paging_ref.is_file():
    text = paging_ref.read_text(encoding="utf-8")
    for term in ["page/pageSize", "LIMIT :limit OFFSET :offset", ">1000", "no duplicates"]:
        if term not in text:
            errors.append(f"{paging_ref.relative_to(root)} missing paging guard: {term}")

deprecation_ref = references[2]
if deprecation_ref.is_file():
    text = deprecation_ref.read_text(encoding="utf-8")
    for term in ["installed version", "official", "@Suppress(\"DEPRECATION\")", "AutoMirrored"]:
        if term not in text:
            errors.append(f"{deprecation_ref.relative_to(root)} missing migration guard: {term}")

compose = skills / "thalarch-compose-ui" / "SKILL.md"
if compose.is_file():
    text = compose.read_text(encoding="utf-8")
    for term in ["48dp", "AutoMirrored", "Premium Engine", "rendered", "thalarch-localization"]:
        if term not in text:
            errors.append(f"{compose.relative_to(root)} missing product-UI guard: {term}")

matching = skills / "thalarch-entity-matching" / "SKILL.md"
if matching.is_file():
    text = matching.read_text(encoding="utf-8")
    for term in ["Unicode", "no confident match", "rank 1", "qualifier"]:
        if term not in text:
            errors.append(f"{matching.relative_to(root)} missing entity-matching guard: {term}")

localization = skills / "thalarch-localization" / "SKILL.md"
if localization.is_file():
    text = localization.read_text(encoding="utf-8")
    for term in ["key parity", "placeholder", "RTL", "default-locale build"]:
        if term not in text:
            errors.append(f"{localization.relative_to(root)} missing localization guard: {term}")

no_regression = skills / "thalarch-no-regression" / "SKILL.md"
if no_regression.is_file():
    text = no_regression.read_text(encoding="utf-8")
    for term in ["Must preserve", "Suspected problem", "AUDIT ONLY", "TARGETED MUTATION", "UNKNOWN"]:
        if term not in text:
            errors.append(f"{no_regression.relative_to(root)} missing no-regression contract term: {term}")

docs = [
    root / "docs" / "ANDROID-ENGINEERING-PACK.md",
    root / "docs" / "ANDROID-TEST-PROMPTS.md",
]
for path in docs:
    if not path.is_file():
        errors.append(f"missing Android pack documentation: {path.relative_to(root)}")

if errors:
    print("THALARCH ANDROID PACK VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH ANDROID PACK VALIDATION PASSED")
print("skills:", ", ".join(required_skills))
print("media3: wired")
print("compose_product_ui: wired")
print("entity_matching: wired")
print("localization: wired")
print("no_regression_contract: wired")
print("android_performance_reference: wired")
print("room_pagination_reference: wired")
print("deprecation_migration_reference: wired")
