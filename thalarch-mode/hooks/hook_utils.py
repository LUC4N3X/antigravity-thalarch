#!/usr/bin/env python3
"""Shared helpers for Thalarch Antigravity hooks.

The helpers intentionally fail open on transcript-shape drift unless a hook can
prove that a proposed action is unsafe or ungrounded. Hard gates should block
known-bad states, not invent certainty about an unknown Antigravity payload.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable


def read_payload() -> dict[str, Any]:
    try:
        value = json.load(__import__("sys").stdin)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False))


def workspace_roots(payload: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for raw in payload.get("workspacePaths") or []:
        try:
            roots.append(Path(str(raw)).expanduser().resolve())
        except Exception:
            continue
    return roots


def candidate_cwds(payload: dict[str, Any], args: dict[str, Any] | None = None) -> list[Path]:
    values: list[Path] = []
    args = args or {}
    for key in ("Cwd", "cwd", "WorkingDirectory", "workingDirectory", "DirectoryPath"):
        raw = args.get(key)
        if raw:
            try:
                values.append(Path(str(raw)).expanduser().resolve())
            except Exception:
                pass
    values.extend(workspace_roots(payload))
    # Preserve order while removing duplicates.
    seen: set[str] = set()
    result: list[Path] = []
    for path in values:
        marker = os.path.normcase(str(path))
        if marker not in seen:
            seen.add(marker)
            result.append(path)
    return result


def resolve_existing_path(raw: str, payload: dict[str, Any], args: dict[str, Any] | None = None) -> Path | None:
    raw = raw.strip().strip('"').strip("'")
    if not raw or raw.startswith(("http://", "https://")):
        return None
    if any(ch in raw for ch in ("*", "?", "[", "]")):
        return None

    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve() if candidate.exists() else None
        except Exception:
            return candidate if candidate.exists() else None

    for cwd in candidate_cwds(payload, args):
        path = cwd / candidate
        if path.exists():
            try:
                return path.resolve()
            except Exception:
                return path
    return None


def path_is_inside_workspace(path: Path, payload: dict[str, Any]) -> bool:
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    for root in workspace_roots(payload):
        try:
            resolved.relative_to(root)
            return True
        except Exception:
            continue
    return False


def transcript_steps(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("transcriptPath")
    if not raw:
        return []
    path = Path(str(raw)).expanduser()
    if not path.is_file():
        return []

    steps: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle):
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except Exception:
                    continue
                if isinstance(value, dict):
                    if "step_index" not in value:
                        value = dict(value)
                        value["_thalarch_line_index"] = line_number
                    steps.append(value)
    except Exception:
        return []
    return steps


def step_order(step: dict[str, Any], fallback: int) -> int:
    raw = step.get("step_index", step.get("stepIndex", step.get("_thalarch_line_index", fallback)))
    try:
        return int(raw)
    except Exception:
        return fallback


def tool_calls(payload: dict[str, Any]) -> list[tuple[int, str, dict[str, Any]]]:
    """Return actual transcript tool calls in trajectory order.

    Antigravity currently records model tool calls in PLANNER_RESPONSE.tool_calls.
    A few compatibility shapes are accepted so minor transcript changes do not
    silently disable the gate.
    """
    calls: list[tuple[int, str, dict[str, Any]]] = []
    for fallback, step in enumerate(transcript_steps(payload)):
        order = step_order(step, fallback)
        raw_calls: list[Any] = []
        for key in ("tool_calls", "toolCalls"):
            value = step.get(key)
            if isinstance(value, list):
                raw_calls.extend(value)
        singular = step.get("toolCall")
        if isinstance(singular, dict):
            raw_calls.append(singular)

        for call in raw_calls:
            if not isinstance(call, dict):
                continue
            name = str(call.get("name") or "").strip()
            args = call.get("args") if isinstance(call.get("args"), dict) else {}
            if name:
                calls.append((order, name, args))
    calls.sort(key=lambda item: item[0])
    return calls


def latest_model_content(payload: dict[str, Any]) -> str:
    candidates: list[tuple[int, str]] = []
    for fallback, step in enumerate(transcript_steps(payload)):
        source = str(step.get("source") or "").upper()
        status = str(step.get("status") or "").upper()
        typ = str(step.get("type") or "").upper()
        content = step.get("content")
        if source == "MODEL" and status in ("", "DONE") and typ == "PLANNER_RESPONSE" and isinstance(content, str):
            candidates.append((step_order(step, fallback), content))
    return max(candidates, key=lambda item: item[0])[1] if candidates else ""


def args_text(args: dict[str, Any]) -> str:
    try:
        return json.dumps(args, ensure_ascii=False, sort_keys=True).lower()
    except Exception:
        return str(args).lower()


def state_file(payload: dict[str, Any], name: str) -> Path | None:
    raw = payload.get("artifactDirectoryPath")
    if not raw:
        return None
    directory = Path(str(raw)).expanduser()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    return directory / f".thalarch-{name}.json"


def load_state(payload: dict[str, Any], name: str) -> dict[str, Any]:
    path = state_file(payload, name)
    if not path or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def save_state(payload: dict[str, Any], name: str, value: dict[str, Any]) -> None:
    path = state_file(payload, name)
    if not path:
        return
    try:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def find_nearest_file(filename: str, payload: dict[str, Any], args: dict[str, Any] | None = None) -> Path | None:
    for cwd in candidate_cwds(payload, args):
        current = cwd
        while True:
            candidate = current / filename
            if candidate.exists():
                return candidate
            if current.parent == current:
                break
            # Do not climb above the containing workspace root when one is known.
            parent = current.parent
            if workspace_roots(payload) and not any(
                _is_relative_to(parent, root) or _is_relative_to(root, parent)
                for root in workspace_roots(payload)
            ):
                break
            current = parent
    return None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False
