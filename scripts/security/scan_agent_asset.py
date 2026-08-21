#!/usr/bin/env python3
"""Static risk scanner for external skills, MCP descriptions, and agent instructions.

Findings are triage signals, not automatic proof of maliciousness. High-risk
matches should trigger provenance review before the content is allowed to direct
commands, secrets, network calls, or policy changes.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

RULES = [
    ("instruction_override", "high", re.compile(r"\b(?:ignore|override|disregard)\b.{0,60}\b(?:previous|system|developer|safety|policy)\b", re.I | re.S)),
    ("secret_exfiltration", "high", re.compile(r"\b(?:send|upload|post|exfiltrat|transmit)\w*\b.{0,80}\b(?:secret|token|credential|password|api[_ -]?key|cookie)\w*\b", re.I | re.S)),
    ("credential_harvest", "high", re.compile(r"\b(?:read|print|cat|dump|collect)\b.{0,80}\b(?:\.env|credentials?|secrets?|ssh|keychain)\b", re.I | re.S)),
    ("disable_guardrails", "high", re.compile(r"\b(?:disable|bypass|remove|turn off)\b.{0,80}\b(?:guard|hook|safety|security|permission|review|verification)\w*\b", re.I | re.S)),
    ("download_execute", "medium", re.compile(r"\b(?:curl|wget|invoke-webrequest)\b.{0,160}(?:\||&&|;)\s*(?:sh|bash|pwsh|powershell|python)\b", re.I | re.S)),
    ("unbounded_shell", "medium", re.compile(r"\b(?:execute|run)\b.{0,60}\b(?:any|arbitrary|whatever)\b.{0,40}\b(?:command|shell|script)\b", re.I | re.S)),
    ("persistence", "medium", re.compile(r"\b(?:startup|autorun|cron|scheduled task|launchagent|registry run)\b", re.I)),
]

TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".ts"}


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    for child in path.rglob("*"):
        if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS and ".git" not in child.parts:
            yield child


def scan_text(text: str, source: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for rule_id, severity, pattern in RULES:
        for match in pattern.finditer(text):
            prefix = text[max(0, match.start() - 24):match.start()].lower()
            if severity == "high" and any(token in prefix for token in ("never ", "do not ", "don't ", "must not ")):
                continue
            excerpt = " ".join(match.group(0).split())[:240]
            findings.append({
                "rule": rule_id,
                "severity": severity,
                "source": source,
                "offset": match.start(),
                "excerpt": excerpt,
            })
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan an external agent asset for instruction/supply-chain risk")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args()

    findings: list[dict[str, object]] = []
    for file in iter_files(args.path):
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        findings.extend(scan_text(text, str(file)))

    result = {
        "path": str(args.path),
        "findings": findings,
        "high": sum(item["severity"] == "high" for item in findings),
        "medium": sum(item["severity"] == "medium" for item in findings),
    }
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"THALARCH SUPPLY-CHAIN SCAN: high={result['high']} medium={result['medium']}")
        for item in findings:
            print(f"[{str(item['severity']).upper()}] {item['rule']} :: {item['source']} :: {item['excerpt']}")
    if args.fail_on_high and result["high"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
