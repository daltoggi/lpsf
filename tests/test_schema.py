import sqlite3

import pytest

from lpsf import db
from tests.conftest import insert_event, insert_mark, insert_snapshot


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


def table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def column_info(conn, table):
    return {row[1]: row for row in conn.execute(f"PRAGMA table_info({table})")}


def test_schema_creates_all_13_tables(conn):
    assert EXPECTED_TABLES.issubset(table_names(conn))


def test_foreign_keys_are_enabled(conn):
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_snapshot_id_is_required_on_all_domain_tables(conn):
    for table in EXPECTED_TABLES - {"evidence_snapshots"}:
        info = column_info(conn, table)
        assert "snapshot_id" in info, table
        assert info["snapshot_id"][3] == 1, table


def test_foreign_keys_reject_missing_snapshot_and_event(conn):
    insert_snapshot(conn)
    with pytest.raises(sqlite3.IntegrityError):
        insert_event(conn, snapshot_id="missing_snapshot")

    with pytest.raises(sqlite3.IntegrityError):
        insert_mark(conn, "mark_missing_event", event_id="missing_event")


def test_json_check_rejects_invalid_evidence_refs(conn):
    insert_snapshot(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO experience_events (
                event_id, sanitized_summary, event_type, importance, novelty, outcome,
                goal_relevance, privacy_level, evidence_refs, snapshot_id, created_at
            )
            VALUES ('evt_bad_json', 'synthetic', 'synthetic', 0, 0, 'observed', 0,
                    'D3', 'not-json', 'snap_test', '2026-05-23T00:00:00Z')
            """
        )


def test_schema_rejects_unbounded_scores(conn):
    insert_snapshot(conn)
    insert_event(conn)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO plasticity_marks (
                mark_id, operator_type, target_type, target_id, strength, half_life,
                source_experience_id, evidence_refs, reason, status, privacy_level,
                scope, snapshot_id, created_at, updated_at, score_delta_meta
            )
            VALUES ('mark_unbounded', 'deepen_attractor', 'path', 'path:synthetic', 2.5,
                    'episodic', 'evt_1', '[]', 'synthetic', 'active', 'D3', 'test',
                    'snap_test', '2026-05-23T00:00:00Z', '2026-05-23T00:00:00Z', '{}')
            """
        )


def test_append_only_blocks_event_update_and_delete(conn):
    insert_snapshot(conn)
    insert_event(conn)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE experience_events SET sanitized_summary='mutated' WHERE event_id='evt_1'"
        )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM experience_events WHERE event_id='evt_1'")


def test_append_only_blocks_trace_update_and_delete(conn):
    insert_snapshot(conn)
    conn.execute(
        """
        INSERT INTO hypothesis_traces (
            trace_id, query_id, candidates, amplitudes, interference_matrix,
            selected_hypothesis, rejected_paths, score_components, snapshot_id, created_at
        )
        VALUES ('hyp_1', 'query_1', '[]', '{}', '{}', 'candidate_a', '[]', '{}',
                'snap_test', '2026-05-23T00:00:00Z')
        """
    )
    conn.execute(
        """
        INSERT INTO collapse_traces (
            trace_id, query_id, selected_path, active_attractors, active_marks,
            evidence_refs, value_contributions, sensitivity_contributions,
            unresolved_tensions, suppressed_paths, warnings, snapshot_id, created_at
        )
        VALUES ('col_1', 'query_1', 'path:synthetic', '[]', '[]', '[]', '{}', '{}',
                '[]', '[]', '[]', 'snap_test', '2026-05-23T00:00:00Z')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE hypothesis_traces SET selected_hypothesis='candidate_b' WHERE trace_id='hyp_1'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM hypothesis_traces WHERE trace_id='hyp_1'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE collapse_traces SET selected_path='path:other' WHERE trace_id='col_1'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM collapse_traces WHERE trace_id='col_1'")


def test_plasticity_marks_are_append_only_except_supersession(conn):
    insert_snapshot(conn)
    insert_event(conn)
    insert_mark(conn, "mark_old")
    insert_mark(conn, "mark_new")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE plasticity_marks SET target_id='path:mutated' WHERE mark_id='mark_old'"
        )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM plasticity_marks WHERE mark_id='mark_old'")

    db.supersede_mark(conn, "mark_old", "mark_new")
    row = conn.execute(
        "SELECT status, supersedes_mark_id FROM plasticity_marks WHERE mark_id='mark_old'"
    ).fetchone()
    assert tuple(row) == ("superseded", "mark_new")

    with pytest.raises(db.AppendOnlyViolation):
        db.supersede_mark(conn, "mark_old", "mark_new")
