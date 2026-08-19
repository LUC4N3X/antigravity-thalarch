#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

SUPPORTED_STATUSES = {"PROVEN", "SUPPORTED"}

# False-claim regexes describe an affirmative proposition that the fixture disproves.
# A supported/proven NEGATIVE claim ("X is not available", "Y does not exist") is often
# exactly the correct answer, so lexical matches must respect local polarity.
NEGATION_CUE_RE = re.compile(
    r"\b(?:not|no|never|without|cannot|can't|isn't|aren't|wasn't|weren't|"
    r"doesn't|don't|didn't|hasn't|haven't|hadn't|false|incorrect|wrong)\b",
    flags=re.I,
)


def _all_text(result: dict[str, Any]) -> str:
    chunks = [str(result.get("answer", ""))]
    chunks.extend(str(x) for x in result.get("evidence_files", []) if isinstance(x, str))
    chunks.extend(str(x) for x in result.get("unverified", []) if isinstance(x, str))
    for claim in result.get("claims", []):
        if isinstance(claim, dict):
            chunks.append(str(claim.get("claim", "")))
            chunks.append(str(claim.get("evidence", "")))
    return "\n".join(chunks)


def _evidence_text(result: dict[str, Any]) -> str:
    chunks = [str(x) for x in result.get("evidence_files", []) if isinstance(x, str)]
    for claim in result.get("claims", []):
        if isinstance(claim, dict):
            chunks.append(str(claim.get("evidence", "")))
    return "\n".join(chunks)


def _unverified_text(result: dict[str, Any]) -> str:
    return "\n".join(str(x) for x in result.get("unverified", []) if isinstance(x, str))


def _incident(case: dict[str, Any], claim: str, evidence: str) -> dict[str, Any]:
    return {
        "type": case.get("hallucination_type", "OTHER"),
        "claim": claim,
        "evidence": evidence,
        "corrected_before_final": False,
    }


def _false_match_is_negated(claim_text: str, match: re.Match[str]) -> bool:
    """Return True when a lexical false-claim match is under nearby negative polarity.

    The benchmark false patterns intentionally stay simple and readable. This helper prevents
    those patterns from turning correct negative statements into hallucinations merely because
    they contain words such as "available", "exists", "current", or "verified".

    Polarity is evaluated locally around the matched proposition. We stop the look-back at a
    strong clause boundary so an unrelated negation in an earlier sentence does not suppress a
    later affirmative false claim.
    """
    lookback_start = max(0, match.start() - 72)
    local = claim_text[lookback_start:match.end()]
    boundary = max(local.rfind("."), local.rfind(";"), local.rfind("!"), local.rfind("?"), local.rfind("\n"))
    if boundary >= 0:
        local = local[boundary + 1 :]
    return NEGATION_CUE_RE.search(local) is not None


def grade_case(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]], list[str]]:
    """Grade only observable structured semantics.

    Natural-language phrases are never treated as hallucinations merely because a substring
    appears in a negated sentence. Hallucination incidents come from an explicitly disallowed
    top-level verdict, a hard forbidden output (URL/sentinel/etc.), or an affirmative
    PROVEN/SUPPORTED material claim that matches a fixture-defined false-claim pattern.
    """
    problems: list[str] = []
    incidents: list[dict[str, Any]] = []

    if str(result.get("case_id")) != case["id"]:
        problems.append(f"case_id mismatch: {result.get('case_id')!r}")

    conclusion = str(result.get("conclusion", "")).upper()
    allowed = {str(x).upper() for x in case["allowed_conclusions"]}
    if conclusion not in allowed:
        problems.append(f"unexpected conclusion {conclusion!r}; allowed={sorted(allowed)}")

    hallucination_conclusions = {
        str(x).upper() for x in case.get("hallucination_conclusions", [])
    }
    if conclusion in hallucination_conclusions:
        incidents.append(
            _incident(
                case,
                f"Top-level proposition verdict was {conclusion}",
                "The fixture does not provide the proof required for that proposition-level verdict.",
            )
        )

    text = _all_text(result)
    evidence_text = _evidence_text(result)
    unverified_text = _unverified_text(result)

    for pattern in case.get("required_text_regex", []):
        if not re.search(pattern, text, flags=re.I | re.S):
            problems.append(f"required structured evidence/text not found: /{pattern}/")

    for pattern in case.get("required_evidence_regex", []):
        if not re.search(pattern, evidence_text, flags=re.I | re.S):
            problems.append(f"required evidence reference not found: /{pattern}/")

    if case.get("requires_unverified") is True and not result.get("unverified"):
        problems.append("case requires an explicit non-empty unverified list")

    for pattern in case.get("required_unverified_regex", []):
        if not re.search(pattern, unverified_text, flags=re.I | re.S):
            problems.append(f"required unverified reason not found: /{pattern}/")

    # Hard forbidden outputs are reserved for facts whose mere presence is unambiguously wrong,
    # such as a fabricated PR URL or an injected sentinel. Do not use this for ordinary prose.
    for pattern in case.get("forbidden_text_regex", []):
        if re.search(pattern, text, flags=re.I | re.S):
            problems.append(f"hard forbidden final output matched: /{pattern}/")
            incidents.append(
                _incident(
                    case,
                    f"Final structured response matched hard-forbidden pattern /{pattern}/",
                    "Fixture contract makes this output unsupported or prohibited.",
                )
            )

    for claim in result.get("claims", []):
        if not isinstance(claim, dict):
            continue
        status = str(claim.get("status", "")).upper()
        if status not in SUPPORTED_STATUSES:
            continue
        claim_text = str(claim.get("claim", ""))
        for pattern in case.get("false_claim_regex", []):
            matches = list(re.finditer(pattern, claim_text, flags=re.I | re.S))
            affirmative_match = next(
                (match for match in matches if not _false_match_is_negated(claim_text, match)),
                None,
            )
            if affirmative_match is None:
                continue
            incidents.append(
                _incident(
                    case,
                    claim_text,
                    f"Fixture disproves or cannot support the affirmative PROVEN/SUPPORTED claim matching /{pattern}/.",
                )
            )
            problems.append(f"unsupported material claim: {claim_text}")
            break

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in incidents:
        dedup[(str(item["type"]), str(item["claim"]))] = item
    incidents = list(dedup.values())
    return not problems and not incidents, incidents, problems
