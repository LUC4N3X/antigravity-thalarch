#!/usr/bin/env python3
"""Deterministic decision gate for Thalarch autoresearch experiments.

Input is a JSON object from a file path or stdin. The helper classifies one candidate
as KEEP, REVERT, or INCONCLUSIVE. It intentionally performs no Git operations, runs no
benchmarks, and mutates no project files.

Example input:
{
  "metric": {
    "name": "latency_ms",
    "direction": "minimize",
    "baseline": 120.0,
    "candidate": 109.0,
    "minimum_improvement": 5.0,
    "noise_tolerance": 2.0
  },
  "guardrails": [
    {"name": "tests", "passed": true},
    {"name": "memory_ceiling", "passed": true}
  ]
}
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

VALID_DIRECTIONS = {"minimize", "maximize"}


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _nonnegative_number(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if number < 0:
        raise ValueError(f"{field} must be >= 0")
    return number


def _guardrail_failures(raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("guardrails must be a list")

    failures: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"guardrails[{index}] must be an object")
        name = item.get("name")
        passed = item.get("passed")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"guardrails[{index}].name must be a non-empty string")
        if not isinstance(passed, bool):
            raise ValueError(f"guardrails[{index}].passed must be boolean")
        if not passed:
            failures.append(name.strip())
    return failures


def decide(payload: dict[str, Any]) -> dict[str, Any]:
    metric = payload.get("metric")
    if not isinstance(metric, dict):
        raise ValueError("metric must be an object")

    name = metric.get("name", "primary")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("metric.name must be a non-empty string")

    direction = metric.get("direction")
    if direction not in VALID_DIRECTIONS:
        allowed = ", ".join(sorted(VALID_DIRECTIONS))
        raise ValueError(f"metric.direction must be one of: {allowed}")

    baseline = _finite_number(metric.get("baseline"), "metric.baseline")
    candidate = _finite_number(metric.get("candidate"), "metric.candidate")
    minimum_improvement = _nonnegative_number(
        metric.get("minimum_improvement", 0.0), "metric.minimum_improvement"
    )
    noise_tolerance = _nonnegative_number(
        metric.get("noise_tolerance", 0.0), "metric.noise_tolerance"
    )

    failures = _guardrail_failures(payload.get("guardrails"))

    improvement = baseline - candidate if direction == "minimize" else candidate - baseline
    required_improvement = max(minimum_improvement, noise_tolerance)

    if failures:
        decision = "REVERT"
        reason = "required_guardrail_failed"
    elif improvement < -noise_tolerance:
        decision = "REVERT"
        reason = "metric_materially_regressed"
    elif improvement > 0 and improvement >= required_improvement:
        decision = "KEEP"
        reason = "metric_improved_and_guardrails_passed"
    else:
        decision = "INCONCLUSIVE"
        reason = "difference_below_meaningful_or_noise_threshold"

    relative_improvement_pct: float | None
    if baseline == 0:
        relative_improvement_pct = None
    else:
        relative_improvement_pct = (improvement / abs(baseline)) * 100.0

    return {
        "decision": decision,
        "reason": reason,
        "metric": name.strip(),
        "direction": direction,
        "baseline": baseline,
        "candidate": candidate,
        "absolute_improvement": improvement,
        "relative_improvement_pct": relative_improvement_pct,
        "minimum_improvement": minimum_improvement,
        "noise_tolerance": noise_tolerance,
        "required_improvement": required_improvement,
        "failed_guardrails": failures,
    }


def _read_payload(path: str) -> dict[str, Any]:
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify one Thalarch autoresearch candidate as KEEP, REVERT, or INCONCLUSIVE."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="JSON input path, or '-' / omitted for stdin",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = decide(_read_payload(args.input))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
