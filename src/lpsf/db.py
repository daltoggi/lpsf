"""SQLite helpers for the M2 storage layer."""

import sqlite3
from pathlib import Path
from typing import Optional, Union

from .errors import AppendOnlyViolation, SchemaError


STATE_DB_VERSION = "0.1.0-M2"
EXPECTED_TABLES = {
    "experience_events",
    "plasticity_marks",
    "attractors",
    "semantic_nodes",
    "semantic_edges",
    "value_field_weights",
    "sensitivity_profiles",
    "schema_mappings",
    "reconsolidation_records",
    "hypothesis_traces",
    "collapse_traces",
    "evidence_snapshots",
    "evaluation_runs",
}


def connect(path: Union[str, Path]) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    _enable_foreign_keys(conn)
    return conn


def init_db(target: Union[str, Path, sqlite3.Connection] = ":memory:") -> sqlite3.Connection:
    conn = target if isinstance(target, sqlite3.Connection) else connect(target)
    conn.row_factory = sqlite3.Row
    _enable_foreign_keys(conn)
    conn.executescript(schema_sql())
    verify_schema(conn)
    return conn


def schema_sql() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    try:
        return schema_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaError(f"Unable to read schema: {schema_path}") from exc


def verify_schema(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    actual = {row["name"] for row in rows}
    missing = EXPECTED_TABLES - actual
    if missing:
        raise SchemaError(f"Missing tables: {sorted(missing)}")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise SchemaError("SQLite foreign key enforcement is disabled")


def supersede_mark(
    conn: sqlite3.Connection,
    mark_id: str,
    replacement_mark_id: str,
    updated_at: Optional[str] = None,
) -> None:
    _transition_mark(
        conn,
        mark_id=mark_id,
        related_mark_id=replacement_mark_id,
        status="superseded",
        relation_column="supersedes_mark_id",
        updated_at=updated_at,
    )


def reverse_mark(
    conn: sqlite3.Connection,
    mark_id: str,
    reversal_mark_id: str,
    updated_at: Optional[str] = None,
) -> None:
    _transition_mark(
        conn,
        mark_id=mark_id,
        related_mark_id=reversal_mark_id,
        status="reversed",
        relation_column="reversed_by_mark_id",
        updated_at=updated_at,
    )


def mark_decayed(
    conn: sqlite3.Connection, mark_id: str, updated_at: Optional[str] = None
) -> None:
    timestamp = updated_at or _utc_timestamp()
    cursor = conn.execute(
        """
        UPDATE plasticity_marks
        SET status = 'decayed', updated_at = ?
        WHERE mark_id = ? AND status = 'active'
        """,
        (timestamp, mark_id),
    )
    if cursor.rowcount != 1:
        raise AppendOnlyViolation(f"Mark cannot be decayed: {mark_id}")


def _transition_mark(
    conn: sqlite3.Connection,
    mark_id: str,
    related_mark_id: str,
    status: str,
    relation_column: str,
    updated_at: Optional[str],
) -> None:
    if mark_id == related_mark_id:
        raise AppendOnlyViolation("A mark cannot transition to itself")
    if relation_column not in {"supersedes_mark_id", "reversed_by_mark_id"}:
        raise AppendOnlyViolation(f"Invalid mark relation column: {relation_column}")

    timestamp = updated_at or _utc_timestamp()
    sql = f"""
        UPDATE plasticity_marks
        SET status = ?, updated_at = ?, {relation_column} = ?
        WHERE mark_id = ? AND status = 'active' AND {relation_column} IS NULL
        """
    try:
        cursor = conn.execute(sql, (status, timestamp, related_mark_id, mark_id))
    except sqlite3.IntegrityError as exc:
        raise AppendOnlyViolation(str(exc)) from exc
    if cursor.rowcount != 1:
        raise AppendOnlyViolation(f"Mark cannot be transitioned: {mark_id}")


def _enable_foreign_keys(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")


def _utc_timestamp() -> str:
    from datetime import datetime

    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
