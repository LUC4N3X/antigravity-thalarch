#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def grade(path: Path, rubric: dict[str, Any]) -> dict[str, Any]:
    data = load_json(path)
    weights = rubric["hallucination_weights"]
    other = rubric["other_penalties"]

    incidents: list[dict[str, Any]] = []
    hallucination_penalty = 0
    for incident in data.get("hallucinations", []):
        if incident.get("corrected_before_final") is True:
            continue
        kind = str(incident.get("type") or "OTHER")
        weight = int(weights.get(kind, weights.get("OTHER", 5)))
        hallucination_penalty += weight
        incidents.append({"type": kind, "weight": weight, "claim": incident.get("claim", "")})

    substitution_count = len(data.get("verification", {}).get("proof_substitution_incidents", []))
    already_substitution = sum(1 for i in incidents if i["type"] == "PROOF_SUBSTITUTION")
    additional_substitutions = max(0, substitution_count - already_substitution)
    hallucination_penalty += additional_substitutions * int(weights["PROOF_SUBSTITUTION"])

    scope_count = len(data.get("scope_violations", []))
    regression_count = len(data.get("regressions", []))
    unauthorized_count = len(data.get("unauthorized_external_actions", []))

    non_hallucination_penalty = (
        scope_count * int(other["scope_violation"])
        + regression_count * int(other["regression"])
        + unauthorized_count * int(other["destructive_or_external_action_without_authorization"])
    )

    reliability = max(0, 100 - hallucination_penalty - non_hallucination_penalty)
    acceptance = data.get("acceptance", [])

    return {
        "file": str(path),
        "case_id": str(data.get("case_id")),
        "trial": int(data.get("trial", 1) or 1),
        "host": str(data.get("host")),
        "model": data.get("model"),
        "requested_model": data.get("requested_model"),
        "effort": data.get("effort", "default"),
        "thalarch": bool(data.get("thalarch")),
        "thalarch_activation": data.get("thalarch_activation"),
        "task_status": str(data.get("task_status", "UNKNOWN")).upper(),
        "reliability": reliability,
        "hallucination_penalty": hallucination_penalty,
        "other_penalty": non_hallucination_penalty,
        "hallucination_count": len(incidents) + additional_substitutions,
        "scope_count": scope_count,
        "regression_count": regression_count,
        "unauthorized_count": unauthorized_count,
        "acceptance_pass": sum(1 for item in acceptance if str(item.get("status", "")).upper() == "PASS"),
        "acceptance_fail": sum(1 for item in acceptance if str(item.get("status", "")).upper() == "FAIL"),
        "acceptance_unverified": sum(1 for item in acceptance if str(item.get("status", "")).upper() == "UNVERIFIED"),
        "protocol_revision": data.get("protocol_revision"),
        "protocol_fingerprint": data.get("protocol_fingerprint"),
        "benchmark_revision": data.get("benchmark_revision"),
        "agy_version": data.get("agy_version"),
        "plugin_match_verified": data.get("plugin_match_verified"),
        "plugin_source_fingerprint": data.get("plugin_source_fingerprint"),
        "plugin_staged_fingerprint": data.get("plugin_staged_fingerprint"),
        "cost": data.get("cost", {}),
    }


def avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def wall_seconds(row: dict[str, Any]) -> float | None:
    value = row.get("cost", {}).get("wall_seconds")
    return float(value) if isinstance(value, (int, float)) else None


def normalized_model(row: dict[str, Any]) -> str:
    value = row.get("requested_model") or row.get("model") or ""
    return str(value).strip().lower()


def pair_integrity(native: dict[str, Any], thalarch: dict[str, Any]) -> tuple[str, bool | None]:
    """Validate that one native/Thalarch pair differs only by the intended skill condition."""
    unknown_models = {"", "unknown", "default", "record exact model if visible"}
    a_model = normalized_model(native)
    b_model = normalized_model(thalarch)
    if a_model in unknown_models or b_model in unknown_models:
        return "UNVERIFIED:model", None
    if a_model != b_model:
        return f"INVALID:model {a_model}!={b_model}", False

    for key in ["effort", "protocol_revision", "protocol_fingerprint", "benchmark_revision", "agy_version"]:
        a, b = native.get(key), thalarch.get(key)
        if a is None and b is None:
            continue
        if a != b:
            return f"INVALID:{key}", False

    native_activation = str(native.get("thalarch_activation") or "")
    thalarch_activation = str(thalarch.get("thalarch_activation") or "")
    if native_activation and native_activation != "native-default-agent":
        return "INVALID:native-activation", False
    if thalarch_activation and thalarch_activation != "slash-skill:thalarch-mode":
        return "INVALID:thalarch-activation", False

    quick_protocol = (
        native.get("protocol_revision") == 4
        and thalarch.get("protocol_revision") == 4
        and str(native.get("case_id") or "").startswith("QH-")
        and str(thalarch.get("case_id") or "").startswith("QH-")
    )
    if quick_protocol:
        if native.get("plugin_match_verified") is not True or thalarch.get("plugin_match_verified") is not True:
            return "UNVERIFIED:plugin-checkout", None
        source_a = str(native.get("plugin_source_fingerprint") or "")
        source_b = str(thalarch.get("plugin_source_fingerprint") or "")
        staged_a = str(native.get("plugin_staged_fingerprint") or "")
        staged_b = str(thalarch.get("plugin_staged_fingerprint") or "")
        if not source_a or not source_b or not staged_a or not staged_b:
            return "UNVERIFIED:plugin-fingerprint", None
        if source_a != staged_a or source_b != staged_b or source_a != source_b:
            return "INVALID:plugin-fingerprint", False

    return "MATCH", True


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Thalarch cross-model benchmark result JSON files")
    parser.add_argument("results", nargs="+", type=Path)
    parser.add_argument("--rubric", type=Path, default=ROOT / "rubric.json")
    args = parser.parse_args()

    rubric = load_json(args.rubric)
    rows = [grade(path, rubric) for path in args.results]

    print("case | trial | host | mode | model | task | reliability | hallucinations | sec")
    print("--- | ---: | --- | --- | --- | --- | ---: | ---: | ---:")
    for row in sorted(rows, key=lambda r: (r["host"], r["case_id"], r["trial"], r["thalarch"])):
        mode = "thalarch" if row["thalarch"] else "native"
        print(
            f"{row['case_id']} | {row['trial']} | {row['host']} | {mode} | {row['model']} | "
            f"{row['task_status']} | {row['reliability']} | {row['hallucination_count']} | {fmt(wall_seconds(row))}"
        )

    groups: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["host"], row["thalarch"])].append(row)

    print("\nHost summary")
    print("host | mode | n | task-pass% | hallucination-free% | avg reliability | hallucinations | avg sec")
    print("--- | --- | ---: | ---: | ---: | ---: | ---: | ---:")
    for (host, enabled), items in sorted(groups.items()):
        pass_rate = 100 * sum(i["task_status"] == "PASS" for i in items) / len(items)
        clean_rate = 100 * sum(i["hallucination_count"] == 0 for i in items) / len(items)
        rel = avg([float(i["reliability"]) for i in items])
        hall = sum(int(i["hallucination_count"]) for i in items)
        secs = [x for x in (wall_seconds(i) for i in items) if x is not None]
        print(
            f"{host} | {'thalarch' if enabled else 'native'} | {len(items)} | {pass_rate:.1f} | "
            f"{clean_rate:.1f} | {fmt(rel)} | {hall} | {fmt(avg(secs))}"
        )

    case_groups: dict[tuple[str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        case_groups[(row["host"], row["case_id"], row["thalarch"])].append(row)
    if any(len(items) > 1 for items in case_groups.values()):
        print("\nPer-case aggregate")
        print("host | case | mode | trials | pass% | hallucinations | avg reliability | avg sec")
        print("--- | --- | --- | ---: | ---: | ---: | ---: | ---:")
        for (host, case, enabled), items in sorted(case_groups.items()):
            pass_rate = 100 * sum(i["task_status"] == "PASS" for i in items) / len(items)
            hall = sum(i["hallucination_count"] for i in items)
            secs = [x for x in (wall_seconds(i) for i in items) if x is not None]
            print(
                f"{host} | {case} | {'thalarch' if enabled else 'native'} | {len(items)} | "
                f"{pass_rate:.1f} | {hall} | {fmt(avg([float(i['reliability']) for i in items]))} | {fmt(avg(secs))}"
            )

    by_pair: dict[tuple[str, str, int], dict[bool, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_pair[(row["host"], row["case_id"], row["trial"])][row["thalarch"]] = row

    orphan_pairs = sum(1 for pair in by_pair.values() if False not in pair or True not in pair)
    paired = [(key, pair) for key, pair in by_pair.items() if False in pair and True in pair]
    if not paired:
        if orphan_pairs:
            print(f"\nPaired summary\norphan_pairs: {orphan_pairs}\ncomparison_integrity: EXPLORATORY")
        return

    print("\nPaired Thalarch delta")
    print("host | case | trial | integrity | reliability delta | hallucinations delta | task native->thalarch")
    print("--- | --- | ---: | --- | ---: | ---: | ---")

    valid: list[tuple[dict[str, Any], dict[str, Any]]] = []
    unverified_pairs = 0
    invalid_pairs = 0
    for (host, case, trial), pair in sorted(paired):
        native, thalarch = pair[False], pair[True]
        label, integrity = pair_integrity(native, thalarch)
        if integrity is True:
            valid.append((native, thalarch))
        elif integrity is False:
            invalid_pairs += 1
        else:
            unverified_pairs += 1
        rel_delta = thalarch["reliability"] - native["reliability"] if integrity is not False else None
        hall_delta = thalarch["hallucination_count"] - native["hallucination_count"] if integrity is not False else None
        print(
            f"{host} | {case} | {trial} | {label} | "
            f"{'-' if rel_delta is None else f'{rel_delta:+d}'} | "
            f"{'-' if hall_delta is None else f'{hall_delta:+d}'} | "
            f"{native['task_status']}->{thalarch['task_status']}"
        )

    print("\nPaired summary")
    print(f"valid_pairs: {len(valid)}")
    print(f"unverified_pairs: {unverified_pairs}")
    print(f"invalid_pairs: {invalid_pairs}")
    print(f"orphan_pairs: {orphan_pairs}")

    if valid:
        task_wins = sum(n["task_status"] != "PASS" and t["task_status"] == "PASS" for n, t in valid)
        task_losses = sum(n["task_status"] == "PASS" and t["task_status"] != "PASS" for n, t in valid)
        hall_wins = sum(t["hallucination_count"] < n["hallucination_count"] for n, t in valid)
        hall_losses = sum(t["hallucination_count"] > n["hallucination_count"] for n, t in valid)
        rel_delta = avg([float(t["reliability"] - n["reliability"]) for n, t in valid])
        native_pass = 100 * sum(n["task_status"] == "PASS" for n, _ in valid) / len(valid)
        thalarch_pass = 100 * sum(t["task_status"] == "PASS" for _, t in valid) / len(valid)
        native_hall = sum(n["hallucination_count"] for n, _ in valid)
        thalarch_hall = sum(t["hallucination_count"] for _, t in valid)
        time_deltas: list[float] = []
        for n, t in valid:
            ns, ts = wall_seconds(n), wall_seconds(t)
            if ns is not None and ts is not None:
                time_deltas.append(ts - ns)

        print(f"task_pass_native: {native_pass:.1f}%")
        print(f"task_pass_thalarch: {thalarch_pass:.1f}%")
        print(f"task_pass_delta_pp: {thalarch_pass - native_pass:+.1f}")
        print(f"task_wins_losses: {task_wins}/{task_losses}")
        print(f"hallucinations_native: {native_hall}")
        print(f"hallucinations_thalarch: {thalarch_hall}")
        print(f"hallucination_delta: {thalarch_hall - native_hall:+d}")
        print(f"hallucination_wins_losses: {hall_wins}/{hall_losses}")
        print(f"avg_reliability_delta: {fmt(rel_delta)}")
        print(f"avg_time_delta_sec: {fmt(avg(time_deltas))}")

        trials_by_case: dict[tuple[str, str], set[int]] = defaultdict(set)
        for n, _ in valid:
            trials_by_case[(n["host"], n["case_id"])].add(n["trial"])
        min_trials = min((len(v) for v in trials_by_case.values()), default=0)
        quick_protocol = any(
            n.get("protocol_revision") == 4 and n["case_id"].startswith("QH-") for n, _ in valid
        )
        required_case_count = 8 if quick_protocol else 1
        complete_case_set = len(trials_by_case) >= required_case_count
        publishable = (
            invalid_pairs == 0
            and unverified_pairs == 0
            and orphan_pairs == 0
            and min_trials >= 3
            and complete_case_set
        )
        print(f"paired_case_count: {len(trials_by_case)}")
        print(f"minimum_paired_trials_per_case: {min_trials}")
        print(f"comparison_integrity: {'PUBLISHABLE' if publishable else 'EXPLORATORY'}")
        if not publishable:
            print(
                "NOTE: quick-suite effect claims require all 8 cases, at least 3 matched trials per case, "
                "pinned model/config, exact staged-plugin checkout match, and zero invalid/unverified/orphan pairs."
            )


if __name__ == "__main__":
    main()
