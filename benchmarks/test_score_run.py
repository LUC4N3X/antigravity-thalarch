#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("thalarch_score_run", HERE / "score_run.py")
assert SPEC and SPEC.loader
score_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score_run)


def base_pair() -> tuple[dict, dict]:
    common = {
        "case_id": "QH-01",
        "host": "antigravity",
        "model": "gemini-3.1-pro-high",
        "requested_model": "gemini-3.1-pro-high",
        "effort": "high",
        "protocol_revision": 4,
        "protocol_fingerprint": "protocol-abc",
        "benchmark_revision": "commit-abc",
        "agy_version": "1.1.15",
        "plugin_match_verified": True,
        "plugin_source_fingerprint": "plugin-abc",
        "plugin_staged_fingerprint": "plugin-abc",
    }
    native = dict(common, thalarch=False, thalarch_activation="native-default-agent")
    thalarch = dict(common, thalarch=True, thalarch_activation="slash-skill:thalarch-mode")
    return native, thalarch


def expect(expected: tuple[str, bool | None], native: dict, thalarch: dict) -> None:
    actual = score_run.pair_integrity(native, thalarch)
    if actual != expected:
        raise AssertionError(f"expected {expected!r}, got {actual!r}")


def main() -> None:
    native, thalarch = base_pair()
    expect(("MATCH", True), native, thalarch)

    missing = copy.deepcopy(thalarch)
    missing["plugin_match_verified"] = None
    expect(("UNVERIFIED:plugin-checkout", None), native, missing)

    mismatch = copy.deepcopy(thalarch)
    mismatch["plugin_staged_fingerprint"] = "plugin-other"
    expect(("INVALID:plugin-fingerprint", False), native, mismatch)

    different_model = copy.deepcopy(thalarch)
    different_model["requested_model"] = "gemini-3.7-flash-high"
    label, valid = score_run.pair_integrity(native, different_model)
    if valid is not False or not label.startswith("INVALID:model "):
        raise AssertionError(f"expected invalid model pair, got {(label, valid)!r}")

    wrong_activation = copy.deepcopy(thalarch)
    wrong_activation["thalarch_activation"] = "thalarch-orchestrator"
    expect(("INVALID:thalarch-activation", False), native, wrong_activation)

    old_protocol = copy.deepcopy(thalarch)
    old_protocol["protocol_revision"] = 3
    expect(("INVALID:protocol_revision", False), native, old_protocol)

    print("THALARCH SCORE RUN REGRESSION TESTS PASSED")


if __name__ == "__main__":
    main()
