#!/usr/bin/env python3
"""Hard-block exact local read targets that do not exist.

This turns a common hallucination pattern — confidently naming a file and then
trying to read it — into a forced search/discovery step.
"""
from pathlib import Path
from typing import Any

from hook_utils import emit, read_payload, resolve_existing_path

READ_TOOLS = {"view_file", "read_file"}
PATH_KEYS = (
    "AbsolutePath",
    "absolutePath",
    "FilePath",
    "filePath",
    "file_path",
    "Path",
    "path",
    "TargetFile",
    "targetFile",
)


def _extract_path(args: dict[str, Any]) -> str | None:
    for key in PATH_KEYS:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def main() -> None:
    payload = read_payload()
    call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
    name = str(call.get("name") or "")
    args = call.get("args") if isinstance(call.get("args"), dict) else {}

    if name not in READ_TOOLS:
        emit({"decision": "allow"})
        return

    raw_path = _extract_path(args)
    if not raw_path:
        # Unknown payload shape: fail open rather than inventing a block.
        emit({"decision": "allow"})
        return

    # URLs and wildcard/glob requests are discovery operations, not exact path claims.
    if raw_path.startswith(("http://", "https://")) or any(ch in raw_path for ch in "*?[]"):
        emit({"decision": "allow"})
        return

    if resolve_existing_path(raw_path, payload, args) is not None:
        emit({"decision": "allow"})
        return

    emit({
        "decision": "deny",
        "reason": (
            f"Thalarch evidence gate: exact read target does not exist in the current workspace: "
            f"{raw_path}. Do not invent the path. Search/list the repository first, identify the "
            "real target, then read that evidence."
        ),
    })


if __name__ == "__main__":
    main()
