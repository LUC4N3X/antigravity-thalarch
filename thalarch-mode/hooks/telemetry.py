#!/usr/bin/env python3
"""Local-first Thalarch telemetry with optional OpenTelemetry spans.

THALARCH_TRACE=off (default), json, or otel. JSON traces are written only inside
the Antigravity artifact directory unless THALARCH_TRACE_FILE is explicitly set.
No network exporter is configured by Thalarch; OpenTelemetry uses the host's
existing SDK/exporter configuration when present.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_VALUE = 1200


def _mode() -> str:
    value = os.environ.get("THALARCH_TRACE", "off").strip().lower()
    return value if value in {"off", "json", "otel"} else "off"


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_VALUE]
    if isinstance(value, list):
        return [_safe(item) for item in value[:50]]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in list(value.items())[:50]:
            lowered = str(key).lower()
            if any(token in lowered for token in ("token", "secret", "password", "authorization", "cookie")):
                result[str(key)] = "<redacted>"
            else:
                result[str(key)] = _safe(child)
        return result
    return str(value)[:MAX_VALUE]


def _json_path(payload: dict[str, Any]) -> Path | None:
    explicit = os.environ.get("THALARCH_TRACE_FILE", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    raw = payload.get("artifactDirectoryPath")
    if not raw:
        return None
    return Path(str(raw)).expanduser() / ".thalarch-trace.jsonl"


def _write_json(payload: dict[str, Any], event: str, fields: dict[str, Any]) -> None:
    path = _json_path(payload)
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **{str(key): _safe(value) for key, value in fields.items()},
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        pass


def _emit_otel(event: str, fields: dict[str, Any]) -> None:
    try:
        from opentelemetry import trace  # type: ignore

        tracer = trace.get_tracer("thalarch")
        with tracer.start_as_current_span(f"thalarch.{event}") as span:
            for key, value in fields.items():
                safe = _safe(value)
                if isinstance(safe, (bool, int, float, str)):
                    span.set_attribute(f"thalarch.{key}", safe)
                else:
                    span.set_attribute(f"thalarch.{key}", json.dumps(safe, ensure_ascii=False))
    except Exception:
        pass


def trace_event(payload: dict[str, Any], event: str, **fields: Any) -> None:
    mode = _mode()
    if mode == "off":
        return
    if mode in {"json", "otel"}:
        _write_json(payload, event, fields)
    if mode == "otel":
        _emit_otel(event, fields)
