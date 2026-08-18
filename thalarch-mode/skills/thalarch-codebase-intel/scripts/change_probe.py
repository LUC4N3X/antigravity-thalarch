#!/usr/bin/env python3
"""Read-only diff/risk snapshot for Thalarch review routing.

This script emits signals, not defects. Material findings must be confirmed in source/runtime.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

EXT_LANG = {
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".py": "python",
    ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
    ".go": "go", ".rs": "rust", ".c": "c", ".cc": "cpp", ".cpp": "cpp",
    ".h": "c-cpp", ".hpp": "cpp", ".cs": "csharp", ".swift": "swift",
    ".dart": "dart", ".rb": "ruby", ".php": "php", ".sql": "sql",
}

PATH_SIGNALS = {
    "security": re.compile(r"(^|/)(auth|security|permission|permissions|acl|oauth|jwt|crypto|secrets?)(/|$)", re.I),
    "data_migration": re.compile(r"(^|/)(migrations?|schema|database|db)(/|$)|\.(sql)$", re.I),
    "ci_release": re.compile(r"(^|/)(\.github/workflows|ci|cd|release|deploy|deployment)(/|$)|Dockerfile$", re.I),
    "api_contract": re.compile(r"(^|/)(api|proto|protos|openapi|graphql)(/|$)|openapi.*\.(ya?ml|json)$", re.I),
    "build_tooling": re.compile(r"(^|/)(gradle|buildSrc|build-logic)(/|$)|(^|/)(pom\.xml|build\.gradle(?:\.kts)?|settings\.gradle(?:\.kts)?|pyproject\.toml|package\.json|Cargo\.toml|go\.mod)$", re.I),
    "ui_visual": re.compile(r"(^|/)(ui|components?|screens?|views?|styles?|assets?)(/|$)|\.(css|scss|sass|less)$", re.I),
}

DIFF_SIGNALS = {
    "concurrency": re.compile(r"\b(synchronized|volatile|Atomic\w*|Lock\b|Executor\w*|CompletableFuture|Thread\b|CoroutineScope|async\b|launch\b|Mutex\b|channel\b|goroutine|go\s+func|tokio::|Arc<|Mutex<)"),
    "security": re.compile(r"\b(auth|authorize|authorization|permission|token|secret|password|credential|crypto|encrypt|decrypt|jwt|oauth)\b", re.I),
    "network_api": re.compile(r"\b(http|https|request|response|endpoint|route|retry|timeout|webhook|grpc|graphql)\b", re.I),
    "persistence": re.compile(r"\b(transaction|repository|entity|hibernate|jpa|database|query|SELECT|INSERT|UPDATE|DELETE|migration|schema)\b", re.I),
}


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=False, timeout=15)


def git_diff_args(base: str | None) -> list[str]:
    return ["git", "diff", f"{base}...HEAD"] if base else ["git", "diff", "HEAD"]


def parse_numstat(text: str) -> tuple[int, int, int]:
    added = deleted = files = 0
    for line in text.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        a, d, _ = parts
        files += 1
        if a.isdigit():
            added += int(a)
        if d.isdigit():
            deleted += int(d)
    return files, added, deleted


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a read-only diff/risk routing snapshot.")
    parser.add_argument("--path", default=".", help="Git workspace path")
    parser.add_argument("--base", help="Base ref for merge-base comparison (base...HEAD). Default: working tree vs HEAD")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args()

    root = Path(ns.path).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")

    inside = run(root, "git", "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0:
        raise SystemExit("Not a Git working tree")

    diff_cmd = git_diff_args(ns.base)
    name_cmd = diff_cmd + ["--name-only"]
    numstat_cmd = diff_cmd + ["--numstat"]
    patch_cmd = diff_cmd + ["--unified=0", "--no-ext-diff"]

    names_p = run(root, *name_cmd)
    numstat_p = run(root, *numstat_cmd)
    patch_p = run(root, *patch_cmd)

    if any(p.returncode != 0 for p in (names_p, numstat_p, patch_p)):
        errors = [p.stderr.strip() for p in (names_p, numstat_p, patch_p) if p.returncode != 0]
        raise SystemExit("Git diff failed: " + " | ".join(errors))

    changed = [line.strip() for line in names_p.stdout.splitlines() if line.strip()]
    files, added, deleted = parse_numstat(numstat_p.stdout)

    languages: Counter[str] = Counter()
    path_signals: dict[str, list[str]] = {key: [] for key in PATH_SIGNALS}
    for path in changed:
        language = EXT_LANG.get(Path(path).suffix.lower())
        if language:
            languages[language] += 1
        normalized = path.replace("\\", "/")
        for label, pattern in PATH_SIGNALS.items():
            if pattern.search(normalized):
                path_signals[label].append(path)

    patch_added = "\n".join(
        line[1:] for line in patch_p.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    content_signals = [label for label, pattern in DIFF_SIGNALS.items() if pattern.search(patch_added)]

    suggested_lenses: list[str] = ["spec/correctness"] if changed else []
    if path_signals["security"] or "security" in content_signals:
        suggested_lenses.append("security")
    if path_signals["data_migration"] or "persistence" in content_signals:
        suggested_lenses.append("data/sql")
    if path_signals["api_contract"] or "network_api" in content_signals:
        suggested_lenses.append("api/compatibility")
    if "concurrency" in content_signals:
        suggested_lenses.append("concurrency/performance")
    if path_signals["ci_release"]:
        suggested_lenses.append("ci/release")
    if path_signals["build_tooling"]:
        suggested_lenses.append("build/dependency")
    if path_signals["ui_visual"]:
        suggested_lenses.append("ui/visual")

    snapshot = {
        "workspace": str(root),
        "comparison": f"{ns.base}...HEAD" if ns.base else "HEAD vs working tree",
        "changed_files": changed,
        "stats": {"files": files, "added": added, "deleted": deleted},
        "languages": dict(languages.most_common()),
        "path_signals": {k: v for k, v in path_signals.items() if v},
        "content_signals": content_signals,
        "suggested_review_lenses": list(dict.fromkeys(suggested_lenses)),
        "disclaimer": "Signals are routing leads, not confirmed defects. Verify material findings in source/runtime.",
    }

    if ns.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(f"Comparison: {snapshot['comparison']}")
        print(f"Changed: {files} files, +{added}/-{deleted}")
        print("Languages:", ", ".join(f"{k}={v}" for k, v in snapshot["languages"].items()) or "none detected")
        print("Path signals:")
        if snapshot["path_signals"]:
            for label, paths in snapshot["path_signals"].items():
                print(f"  {label}: {', '.join(paths)}")
        else:
            print("  none")
        print("Content signals:", ", ".join(content_signals) or "none")
        print("Suggested review lenses:", ", ".join(snapshot["suggested_review_lenses"]) or "none")
        print(snapshot["disclaimer"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
