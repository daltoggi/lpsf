import json

from lpsf.operators import deepen_attractor, weaken_attractor

from tests.operators.conftest import fetch_mark, json_field


def test_weaken_attractor_raises_threshold_and_records_reversible_mark(
    conn, event_id, snapshot_id, evidence_refs
):
    target_id = "path:just-rag"
    deepen_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.5,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="synthetic precondition",
    )
    before = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ?", (target_id,)
    ).fetchone()

    weakened = weaken_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.3,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="correction: not ordinary RAG",
        score_delta_meta={"path_priority": -0.3},
    )

    after = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ?", (target_id,)
    ).fetchone()
    assert after["activation_threshold"] > before["activation_threshold"]
    assert after["depth"] < before["depth"]
    assert json_field(fetch_mark(conn, weakened["mark_id"]), "score_delta_meta")[
        "path_priority"
    ] < 0

    conn.execute(
        """
        INSERT INTO collapse_traces (
            trace_id, query_id, selected_path, active_attractors, active_marks,
            evidence_refs, value_contributions, sensitivity_contributions,
            unresolved_tensions, suppressed_paths, warnings, snapshot_id, created_at
        )
        VALUES ('collapse:weaken', 'query:synthetic', ?, '[]', ?, '["ev:fixture"]',
                '{}', '{}', '[]', ?, '["correction: not ordinary RAG"]', ?,
                '2026-05-23T00:00:00Z')
        """,
        (
            target_id,
            json.dumps([weakened["mark_id"]]),
            json.dumps([{"path": target_id, "reason": "correction: not ordinary RAG"}]),
            snapshot_id,
        ),
    )

    reversal = deepen_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.2,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="later successful evidence",
    )
    old_weaken = fetch_mark(conn, weakened["mark_id"])
    assert old_weaken["status"] == "superseded"
    assert old_weaken["supersedes_mark_id"] == reversal["mark_id"]
