import pytest

from lpsf import db


@pytest.fixture
def conn():
    connection = db.init_db(":memory:")
    try:
        yield connection
    finally:
        connection.close()


def insert_snapshot(connection, snapshot_id="snap_test"):
    connection.execute(
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
        VALUES (?, 'test-0', '[]', '{}', '{}', '{}', '[]', '2026-05-23T00:00:00Z', '2026-05-23T00:00:00Z')
        """,
        (snapshot_id,),
    )
    return snapshot_id


def insert_event(connection, snapshot_id="snap_test", event_id="evt_1"):
    connection.execute(
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
        VALUES (?, 'synthetic event', 'synthetic', 0.5, 0.4, 'observed', 0.7, 'D3', '[]', ?, '2026-05-23T00:00:00Z')
        """,
        (event_id, snapshot_id),
    )
    return event_id


def insert_mark(connection, mark_id, event_id="evt_1", snapshot_id="snap_test"):
    connection.execute(
        """
        INSERT INTO plasticity_marks (
            mark_id,
            operator_type,
            target_type,
            target_id,
            strength,
            half_life,
            source_experience_id,
            evidence_refs,
            reason,
            status,
            privacy_level,
            scope,
            snapshot_id,
            created_at,
            updated_at,
            score_delta_meta
        )
        VALUES (?, 'deepen_attractor', 'path', 'path:synthetic', 0.25, 'episodic', ?, '[]',
                'synthetic reason', 'active', 'D3', 'test', ?, '2026-05-23T00:00:00Z',
                '2026-05-23T00:00:00Z', '{}')
        """,
        (mark_id, event_id, snapshot_id),
    )
    return mark_id
