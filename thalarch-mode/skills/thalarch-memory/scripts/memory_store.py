#!/usr/bin/env python3
"""Portable opt-in durable memory store for Thalarch.

This helper is deliberately small and dependency-free. It stores only compact PROJECT/GENERAL
memory records. SESSION state belongs in the active task ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"
VALID_SCOPES = {"PROJECT", "GENERAL"}
VALID_EVIDENCE = {"SUPPORTED", "PROVEN"}
WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize(text: str) -> str:
    return " ".join(WORD_RE.findall(text.casefold()))


def tokens(text: str) -> set[str]:
    return {token for token in WORD_RE.findall(text.casefold()) if len(token) > 1}


def default_db() -> Path:
    return Path.home() / ".thalarch" / "knowledge" / "memory.sqlite3"


def connect(path: Path) -> sqlite3.Connection:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            kind TEXT NOT NULL,
            project TEXT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            trigger_text TEXT NOT NULL DEFAULT '',
            transfer TEXT NOT NULL DEFAULT '',
            counterexample TEXT NOT NULL DEFAULT '',
            tags_json TEXT NOT NULL DEFAULT '[]',
            evidence TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            confidence REAL NOT NULL,
            generalizable INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            fingerprint TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_memories_scope_project
        ON memories(scope, project, status);
        """
    )
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (SCHEMA_VERSION,),
    )
    conn.commit()


def fingerprint_for(args: argparse.Namespace) -> str:
    payload = "\x1f".join(
        [
            args.scope.upper(),
            (args.project or "").strip().casefold(),
            args.kind.strip().casefold(),
            normalize(args.title),
            normalize(args.body),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_add(args: argparse.Namespace) -> tuple[str, str]:
    scope = args.scope.upper()
    evidence = args.evidence.upper()
    if scope not in VALID_SCOPES:
        raise SystemExit(f"durable scope must be one of: {', '.join(sorted(VALID_SCOPES))}")
    if evidence not in VALID_EVIDENCE:
        raise SystemExit("durable memory requires SUPPORTED or PROVEN evidence")
    if scope == "PROJECT" and not (args.project or "").strip():
        raise SystemExit("PROJECT memory requires --project")
    if scope == "GENERAL":
        if evidence != "PROVEN":
            raise SystemExit("GENERAL memory requires PROVEN evidence")
        if not args.generalizable:
            raise SystemExit("GENERAL memory requires explicit --generalizable")
    if not 0.0 <= args.confidence <= 1.0:
        raise SystemExit("--confidence must be between 0 and 1")
    return scope, evidence


def command_init(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        init_db(conn)
    print(json.dumps({"status": "ok", "db": str(args.db.expanduser())}, ensure_ascii=False))


def command_add(args: argparse.Namespace) -> None:
    scope, evidence = validate_add(args)
    tags = sorted({t.strip().casefold() for t in args.tags.split(",") if t.strip()})
    fp = fingerprint_for(args)
    memory_id = fp[:20]
    created = now_iso()
    expires_at = None
    if args.ttl_days is not None:
        if args.ttl_days <= 0:
            raise SystemExit("--ttl-days must be > 0")
        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=args.ttl_days)
        ).replace(microsecond=0).isoformat()

    with connect(args.db) as conn:
        init_db(conn)
        existing = conn.execute(
            "SELECT id, evidence, confidence FROM memories WHERE fingerprint = ?",
            (fp,),
        ).fetchone()
        if existing:
            confidence = max(float(existing["confidence"]), args.confidence)
            evidence_out = "PROVEN" if "PROVEN" in {existing["evidence"], evidence} else "SUPPORTED"
            conn.execute(
                """
                UPDATE memories
                SET evidence=?, confidence=?, source=?, transfer=?, counterexample=?, tags_json=?,
                    trigger_text=?, status='active', updated_at=?, expires_at=?, generalizable=?
                WHERE fingerprint=?
                """,
                (
                    evidence_out,
                    confidence,
                    args.source,
                    args.transfer,
                    args.counterexample,
                    json.dumps(tags, ensure_ascii=False),
                    args.trigger,
                    created,
                    expires_at,
                    int(args.generalizable),
                    fp,
                ),
            )
            conn.commit()
            memory_id = existing["id"]
            action = "updated"
        else:
            conn.execute(
                """
                INSERT INTO memories(
                    id, scope, kind, project, title, body, trigger_text, transfer, counterexample,
                    tags_json, evidence, source, confidence, generalizable, status, fingerprint,
                    created_at, updated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    scope,
                    args.kind.strip(),
                    (args.project or "").strip() or None,
                    args.title.strip(),
                    args.body.strip(),
                    args.trigger.strip(),
                    args.transfer.strip(),
                    args.counterexample.strip(),
                    json.dumps(tags, ensure_ascii=False),
                    evidence,
                    args.source.strip(),
                    args.confidence,
                    int(args.generalizable),
                    fp,
                    created,
                    created,
                    expires_at,
                ),
            )
            conn.commit()
            action = "created"

    print(json.dumps({"status": "ok", "action": action, "id": memory_id}, ensure_ascii=False))


def row_payload(row: sqlite3.Row, score: float | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": row["id"],
        "scope": row["scope"],
        "kind": row["kind"],
        "project": row["project"],
        "title": row["title"],
        "body": row["body"],
        "trigger": row["trigger_text"],
        "transfer": row["transfer"],
        "counterexample": row["counterexample"],
        "tags": json.loads(row["tags_json"]),
        "evidence": row["evidence"],
        "source": row["source"],
        "confidence": row["confidence"],
        "generalizable": bool(row["generalizable"]),
        "status": row["status"],
        "updated_at": row["updated_at"],
        "expires_at": row["expires_at"],
    }
    if score is not None:
        payload["score"] = round(score, 4)
    return payload


def is_expired(row: sqlite3.Row) -> bool:
    expires = row["expires_at"]
    return bool(expires and expires <= now_iso())


def score_row(row: sqlite3.Row, query: str, project: str | None) -> float:
    q_norm = normalize(query)
    q_tokens = tokens(query)
    title_norm = normalize(row["title"])
    body_norm = normalize(" ".join([row["body"], row["trigger_text"], row["transfer"]]))
    tags = set(json.loads(row["tags_json"]))
    score = 0.0

    if q_norm and q_norm in f"{title_norm} {body_norm}":
        score += 5.0
    for token in q_tokens:
        if token in title_norm.split():
            score += 3.0
        if token in body_norm.split():
            score += 1.0
        if token in tags:
            score += 2.0
    if project and row["project"] and project.casefold() == row["project"].casefold():
        score += 2.0
    if row["evidence"] == "PROVEN":
        score += 0.5
    return score * (0.5 + float(row["confidence"]))


def command_search(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        init_db(conn)
        sql = "SELECT * FROM memories WHERE status='active'"
        params: list[Any] = []
        if args.scope:
            sql += " AND scope=?"
            params.append(args.scope.upper())
        if args.project:
            sql += " AND (project=? OR scope='GENERAL')"
            params.append(args.project)
        rows = conn.execute(sql, params).fetchall()

    scored = []
    for row in rows:
        if is_expired(row):
            continue
        score = score_row(row, args.query, args.project)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], item[1]["updated_at"], item[1]["id"]))
    result = [row_payload(row, score) for score, row in scored[: args.limit]]
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_list(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        init_db(conn)
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list[Any] = []
        if args.scope:
            sql += " AND scope=?"
            params.append(args.scope.upper())
        if args.project:
            sql += " AND project=?"
            params.append(args.project)
        if not args.include_retired:
            sql += " AND status='active'"
        sql += " ORDER BY updated_at DESC, id"
        rows = conn.execute(sql, params).fetchall()
    print(json.dumps([row_payload(row) for row in rows], ensure_ascii=False, indent=2))


def command_retire(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        init_db(conn)
        cursor = conn.execute(
            "UPDATE memories SET status='retired', updated_at=? WHERE id=? AND status!='retired'",
            (now_iso(), args.id),
        )
        conn.commit()
    if cursor.rowcount != 1:
        raise SystemExit(f"active memory not found: {args.id}")
    print(json.dumps({"status": "ok", "action": "retired", "id": args.id}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Thalarch portable durable memory store")
    parser.add_argument("--db", type=Path, default=default_db(), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.set_defaults(func=command_init)

    add = sub.add_parser("add")
    add.add_argument("--scope", required=True, choices=["PROJECT", "GENERAL", "project", "general"])
    add.add_argument("--kind", required=True)
    add.add_argument("--project")
    add.add_argument("--title", required=True)
    add.add_argument("--body", required=True)
    add.add_argument("--trigger", default="")
    add.add_argument("--transfer", default="")
    add.add_argument("--counterexample", default="")
    add.add_argument("--tags", default="")
    add.add_argument("--evidence", required=True, choices=["SUPPORTED", "PROVEN", "supported", "proven"])
    add.add_argument("--source", default="")
    add.add_argument("--confidence", type=float, default=0.8)
    add.add_argument("--generalizable", action="store_true")
    add.add_argument("--ttl-days", type=int)
    add.set_defaults(func=command_add)

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--scope", choices=["PROJECT", "GENERAL", "project", "general"])
    search.add_argument("--project")
    search.add_argument("--limit", type=int, default=8)
    search.set_defaults(func=command_search)

    listing = sub.add_parser("list")
    listing.add_argument("--scope", choices=["PROJECT", "GENERAL", "project", "general"])
    listing.add_argument("--project")
    listing.add_argument("--include-retired", action="store_true")
    listing.set_defaults(func=command_list)

    retire = sub.add_parser("retire")
    retire.add_argument("--id", required=True)
    retire.set_defaults(func=command_retire)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "limit", 1) <= 0:
        raise SystemExit("--limit must be > 0")
    args.func(args)


if __name__ == "__main__":
    main()
