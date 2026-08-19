#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []

skill = root / "thalarch-mode" / "skills" / "thalarch-autoresearch" / "SKILL.md"
gate = root / "thalarch-mode" / "skills" / "thalarch-autoresearch" / "scripts" / "experiment_gate.py"
plugin = root / "thalarch-mode" / "plugin.json"
installer = root / "installers" / "install_adapter.py"

for path in [skill, gate, plugin, installer]:
    if not path.exists():
        errors.append(f"missing autoresearch file: {path.relative_to(root)}")

if skill.exists():
    text = skill.read_text(encoding="utf-8")
    required_terms = [
        "name: thalarch-autoresearch",
        "KEEP",
        "REVERT",
        "INCONCLUSIVE",
        "experiment budget",
        "noise tolerance",
        "correctness guardrails",
        "Self-improvement boundary",
        "thalarch-compound",
        "thalarch-git",
        "Never compare cold vs warm",
    ]
    for term in required_terms:
        if term not in text:
            errors.append(f"thalarch-autoresearch missing required contract: {term}")

if plugin.exists():
    try:
        data = json.loads(plugin.read_text(encoding="utf-8"))
        if "autoresearch" not in data.get("description", "").lower():
            errors.append("plugin description must advertise autoresearch for host discovery")
    except Exception as exc:
        errors.append(f"invalid plugin.json while validating autoresearch: {exc}")

if installer.exists():
    installer_text = installer.read_text(encoding="utf-8")
    if 'source.name.startswith("thalarch-")' not in installer_text:
        errors.append("adapter installer must continue auto-copying canonical thalarch-* skills")

if gate.exists():
    try:
        spec = importlib.util.spec_from_file_location("thalarch_experiment_gate", gate)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not create import spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cases = [
            (
                "minimize_keep",
                {
                    "metric": {
                        "name": "latency_ms",
                        "direction": "minimize",
                        "baseline": 100.0,
                        "candidate": 90.0,
                        "minimum_improvement": 5.0,
                        "noise_tolerance": 2.0,
                    },
                    "guardrails": [{"name": "tests", "passed": True}],
                },
                "KEEP",
            ),
            (
                "maximize_keep",
                {
                    "metric": {
                        "name": "score",
                        "direction": "maximize",
                        "baseline": 70.0,
                        "candidate": 76.0,
                        "minimum_improvement": 3.0,
                        "noise_tolerance": 1.0,
                    },
                    "guardrails": [],
                },
                "KEEP",
            ),
            (
                "guardrail_revert",
                {
                    "metric": {
                        "name": "latency_ms",
                        "direction": "minimize",
                        "baseline": 100.0,
                        "candidate": 80.0,
                        "minimum_improvement": 5.0,
                        "noise_tolerance": 1.0,
                    },
                    "guardrails": [{"name": "tests", "passed": False}],
                },
                "REVERT",
            ),
            (
                "regression_revert",
                {
                    "metric": {
                        "name": "score",
                        "direction": "maximize",
                        "baseline": 80.0,
                        "candidate": 75.0,
                        "minimum_improvement": 2.0,
                        "noise_tolerance": 1.0,
                    },
                    "guardrails": [],
                },
                "REVERT",
            ),
            (
                "noise_inconclusive",
                {
                    "metric": {
                        "name": "latency_ms",
                        "direction": "minimize",
                        "baseline": 100.0,
                        "candidate": 99.5,
                        "minimum_improvement": 2.0,
                        "noise_tolerance": 1.0,
                    },
                    "guardrails": [],
                },
                "INCONCLUSIVE",
            ),
            (
                "zero_threshold_requires_real_improvement",
                {
                    "metric": {
                        "name": "score",
                        "direction": "maximize",
                        "baseline": 5.0,
                        "candidate": 5.0,
                        "minimum_improvement": 0.0,
                        "noise_tolerance": 0.0,
                    },
                    "guardrails": [],
                },
                "INCONCLUSIVE",
            ),
        ]

        for name, payload, expected in cases:
            result = module.decide(payload)
            actual = result.get("decision")
            if actual != expected:
                errors.append(f"experiment gate case {name}: expected {expected}, got {actual}")

        invalid_payloads = [
            {
                "metric": {
                    "name": "score",
                    "direction": "sideways",
                    "baseline": 1,
                    "candidate": 2,
                }
            },
            {
                "metric": {
                    "name": "score",
                    "direction": "maximize",
                    "baseline": 1,
                    "candidate": 2,
                    "noise_tolerance": -1,
                }
            },
        ]
        for payload in invalid_payloads:
            try:
                module.decide(payload)
            except ValueError:
                pass
            else:
                errors.append("experiment gate accepted an invalid contract")
    except Exception as exc:
        errors.append(f"experiment gate validation failed: {exc}")

if errors:
    print("THALARCH AUTORESEARCH VALIDATION FAILED")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("THALARCH AUTORESEARCH VALIDATION PASSED")
print("bounded_loop: enforced")
print("deterministic_decision_gate: enforced")
print("guardrails_before_score: enforced")
print("self_improvement_boundary: enforced")
print("adapter_skill_copy: compatible")
