from lpsf.operators import deepen_attractor

from tests.operators.conftest import fetch_mark, insert_collapse_trace, json_field


def test_deepen_attractor_increases_depth_and_can_be_cited_in_collapse_trace(
    conn, event_id, snapshot_id, evidence_refs
):
    target_id = "path:landscape-memory"

    result = deepen_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.4,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="synthetic accepted interpretation",
    )

    assert set(result) == {"mark_id", "state_delta", "warnings"}
    assert result["state_delta"]["depth_delta"] > 0
    assert result["warnings"] == []

    attractor = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ? AND snapshot_id = ?",
        (target_id, snapshot_id),
    ).fetchone()
    assert attractor["depth"] == 0.4
    assert attractor["activation_threshold"] < 1.0
    assert result["mark_id"] in json_field(dict(attractor), "source_marks")

    mark = fetch_mark(conn, result["mark_id"])
    assert mark["operator_type"] == "deepen_attractor"
    assert mark["source_experience_id"] == event_id
    assert json_field(mark, "evidence_refs") == evidence_refs

    insert_collapse_trace(
        conn,
        trace_id="collapse:deepen",
        snapshot_id=snapshot_id,
        selected_path=target_id,
        mark_id=result["mark_id"],
    )
    trace = conn.execute(
        "SELECT * FROM collapse_traces WHERE trace_id = 'collapse:deepen'"
    ).fetchone()
    assert result["mark_id"] in json_field(dict(trace), "active_marks")
