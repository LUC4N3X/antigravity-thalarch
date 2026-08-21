#!/usr/bin/env python3
"""Resolve pinned host CLI argv templates without guessing vendor flags."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MATRIX_PATH = HERE / "host_matrix.json"


def load_matrix() -> dict[str, Any]:
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def command_template(host: str, explicit_json: str | None = None) -> list[str]:
    matrix = load_matrix()
    hosts = matrix.get("hosts") if isinstance(matrix.get("hosts"), dict) else {}
    config = hosts.get(host) if isinstance(hosts.get(host), dict) else None
    if config is None:
        raise ValueError(f"Unknown benchmark host: {host}")
    raw = explicit_json
    if raw is None:
        env_name = str(config.get("command_env") or "")
        raw = os.environ.get(env_name, "") if env_name else ""
    if not raw:
        raise ValueError(
            f"No pinned command template configured for {host}. Set {config.get('command_env')} "
            "to a JSON argv array or pass --command-json."
        )
    value = json.loads(raw)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError("Host command template must be a non-empty JSON array of non-empty strings")
    return value


def render_command(template: list[str], *, prompt: str, workspace: Path, model: str) -> list[str]:
    values = {
        "{prompt}": prompt,
        "{workspace}": str(workspace),
        "{model}": model,
    }
    rendered: list[str] = []
    for item in template:
        text = item
        for marker, value in values.items():
            text = text.replace(marker, value)
        rendered.append(text)
    return rendered
