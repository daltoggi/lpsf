import json

import pytest

from lpsf import db
from lpsf.adapter import NullAdapter


@pytest.fixture
def conn():
    connection = db.init_db(":memory:")
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def null_adapter():
    return NullAdapter()


@pytest.fixture
def snapshot_id(conn):
    value = "snap_ops"
    conn.execute(
        """
        INSERT INTO evidence_snapshots (
            snapshot_id,
            adapter_version,
            allowed_scope,
            source_counts,
            index_metadata,
            retrieval_parameters,
            drift_observations,
            created_at,
            pinned_at
        )
        VALUES (?, 'null-0', '[]', '{}', '{}', '{}', '[]',
                '2026-05-23T00:00:00Z', '2026-05-23T00:00:00Z')
        """,
        (value,),
    )
    return value


@pytest.fixture
def event_id(conn, snapshot_id):
    value = "evt_ops"
    conn.execute(
        """
        INSERT INTO experience_events (
            event_id,
            sanitized_summary,
            event_type,
            importance,
            novelty,
            outcome,
            goal_relevance,
            privacy_level,
            evidence_refs,
            snapshot_id,
            created_at
        )
        VALUES (?, 'synthetic operator event', 'synthetic', 0.6, 0.4,
                'accepted', 0.8, 'D3', '["ev:fixture"]', ?,
                '2026-05-23T00:00:00Z')
        """,
        (value, snapshot_id),
    )
    return value


@pytest.fixture
def evidence_refs():
    return ["ev:fixture"]


def fetch_one(conn, table, where_column, value):
    row = conn.execute(
        f"SELECT * FROM {table} WHERE {where_column} = ?", (value,)
    ).fetchone()
    assert row is not None
    return dict(row)


def fetch_mark(conn, mark_id):
    return fetch_one(conn, "plasticity_marks", "mark_id", mark_id)


def json_field(row, key):
    return json.loads(row[key])


def insert_collapse_trace(conn, *, trace_id, snapshot_id, selected_path, mark_id):
    conn.execute(
        """
        INSERT INTO collapse_traces (
            trace_id,
            query_id,
            selected_path,
            active_attractors,
            active_marks,
            evidence_refs,
            value_contributions,
            sensitivity_contributions,
            unresolved_tensions,
            suppressed_paths,
            warnings,
            snapshot_id,
            created_at
        )
        VALUES (?, 'query:synthetic', ?, '[]', ?, '["ev:fixture"]',
                '{}', '{}', '[]', '[]', '[]', ?,
                '2026-05-23T00:00:00Z')
        """,
        (trace_id, selected_path, json.dumps([mark_id]), snapshot_id),
    )
