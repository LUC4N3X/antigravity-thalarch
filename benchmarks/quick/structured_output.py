#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from typing import Any, Iterable

RESPONSE_FIELDS = {"case_id", "conclusion", "answer", "claims", "evidence_files", "unverified"}
CONCLUSIONS = {"PROVEN", "CORRECTED_PREMISE", "NOT_FOUND", "UNVERIFIED", "UNKNOWN"}
CLAIM_STATUSES = {"PROVEN", "SUPPORTED", "INFERENCE", "UNKNOWN", "UNVERIFIED", "DISPROVEN"}
CASE_ID_RE = re.compile(r"^QH-\d{2}$")
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
JSON_DECODER = json.JSONDecoder()


def walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def validate_structured_response(obj: Any) -> list[str]:
    """Validate the benchmark answer contract semantically, not by field-name coincidence."""
    errors: list[str] = []
    if not isinstance(obj, dict):
        return ["response is not an object"]

    missing = RESPONSE_FIELDS - set(obj)
    extra = set(obj) - RESPONSE_FIELDS
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected fields: " + ", ".join(sorted(extra)))
    if errors:
        return errors

    case_id = obj.get("case_id")
    conclusion = obj.get("conclusion")
    answer = obj.get("answer")
    claims = obj.get("claims")
    evidence_files = obj.get("evidence_files")
    unverified = obj.get("unverified")

    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id.strip()):
        errors.append("case_id must be a QH-01..QH-99 style benchmark id")
    if not isinstance(conclusion, str) or conclusion not in CONCLUSIONS:
        errors.append("conclusion must be one of the benchmark verdict enums")
    if not isinstance(answer, str):
        errors.append("answer must be a string")

    if not isinstance(claims, list):
        errors.append("claims must be a list")
    else:
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(f"claims[{index}] must be an object")
                continue
            if set(claim) != {"claim", "status", "evidence"}:
                errors.append(f"claims[{index}] fields do not match the schema")
                continue
            if not isinstance(claim.get("claim"), str):
                errors.append(f"claims[{index}].claim must be a string")
            if not isinstance(claim.get("status"), str) or claim.get("status") not in CLAIM_STATUSES:
                errors.append(f"claims[{index}].status must be a valid epistemic status")
            if not isinstance(claim.get("evidence"), str):
                errors.append(f"claims[{index}].evidence must be a string")

    for name, value in (("evidence_files", evidence_files), ("unverified", unverified)):
        if not isinstance(value, list):
            errors.append(f"{name} must be a list")
        elif not all(isinstance(item, str) for item in value):
            errors.append(f"{name} must contain only strings")

    return errors


def _json_objects_from_text(value: Any, *, max_depth: int = 3) -> Iterable[dict[str, Any]]:
    """Recover JSON objects from common CLI wrappers without relaxing the response contract."""
    if not isinstance(value, str) or not value.strip() or max_depth < 0:
        return

    text = value.strip()
    fence = FENCE_RE.match(text)
    if fence:
        text = fence.group(1).strip()

    # Fast path: the entire string is JSON. Recurse if it is a JSON-encoded string.
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        yield parsed
    elif isinstance(parsed, str) and parsed != text and max_depth > 0:
        yield from _json_objects_from_text(parsed, max_depth=max_depth - 1)

    # Robust path: locate JSON objects embedded in prose or stream wrapper text.
    positions = [idx for idx, char in enumerate(text) if char == "{"]
    for start in positions:
        try:
            parsed, _end = JSON_DECODER.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            yield parsed
        elif isinstance(parsed, str) and max_depth > 0:
            yield from _json_objects_from_text(parsed, max_depth=max_depth - 1)


def _response_candidates(events: list[dict[str, Any]], stdout: str) -> Iterable[dict[str, Any]]:
    """Yield candidates newest-first while preferring known final-result wrapper fields."""
    seen: set[str] = set()

    def emit(candidate: Any):
        if not isinstance(candidate, dict):
            return
        try:
            marker = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError):
            marker = repr(candidate)
        if marker in seen:
            return
        seen.add(marker)
        yield candidate

    preferred_keys = ("result", "output", "response", "content", "text", "message")
    for event in reversed(events):
        for obj in walk(event):
            if not isinstance(obj, dict):
                continue
            for key in preferred_keys:
                value = obj.get(key)
                if isinstance(value, dict):
                    yield from emit(value)
                elif isinstance(value, str):
                    for parsed in _json_objects_from_text(value):
                        yield from emit(parsed)
            yield from emit(obj)

    # Some CLI variants include non-NDJSON final text. Scan the raw stdout as a last resort.
    for parsed in _json_objects_from_text(stdout):
        yield from emit(parsed)


def extract_result(events: list[dict[str, Any]], stdout: str) -> dict[str, Any] | None:
    """Return only a semantically conformant benchmark answer; never accept an echoed JSON Schema."""
    for candidate in _response_candidates(events, stdout):
        if not validate_structured_response(candidate):
            return candidate
    return None


def response_like_diagnostics(events: list[dict[str, Any]], stdout: str = "") -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for candidate in _response_candidates(events, stdout):
        if not (set(candidate) & RESPONSE_FIELDS):
            continue
        problems = validate_structured_response(candidate)
        if not problems:
            continue
        signature = "; ".join(problems)
        if signature in seen:
            continue
        seen.add(signature)
        diagnostics.append(signature)
        if len(diagnostics) >= 4:
            break
    return diagnostics


def install_into(runner: Any) -> None:
    """Install the hardened extractor into the legacy low-level runner used by run_pair.py."""
    runner.RESPONSE_FIELDS = RESPONSE_FIELDS
    runner.CONCLUSIONS = CONCLUSIONS
    runner.CLAIM_STATUSES = CLAIM_STATUSES
    runner.validate_structured_response = validate_structured_response
    runner.extract_result = extract_result

    # The legacy diagnostic callback accepts only events. Preserve that signature while letting the
    # hardened extractor perform the actual run-time isolation.
    runner.response_like_diagnostics = lambda events: response_like_diagnostics(events)
