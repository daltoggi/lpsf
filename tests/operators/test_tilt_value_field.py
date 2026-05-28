from lpsf.operators import tilt_value_field

from tests.operators.conftest import fetch_mark, json_field


def test_tilt_value_field_changes_axis_weight_and_supersedes_prior_mark(
    conn, event_id, snapshot_id, evidence_refs
):
    first = tilt_value_field(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        axis_name="source_grounding",
        strength=0.3,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="prefer traceable evidence",
        scope="project",
    )
    second = tilt_value_field(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        axis_name="source_grounding",
        strength=0.2,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="repeat same value tilt",
        scope="project",
    )

    row = conn.execute(
        """
        SELECT * FROM value_field_weights
        WHERE axis_name = 'source_grounding' AND scope = 'project'
        """
    ).fetchone()
    assert row["weight"] == 0.5
    assert second["mark_id"] in json_field(dict(row), "source_marks")
    assert json_field(dict(row), "score_contribution_meta")["latest_delta"] == 0.2

    old_mark = fetch_mark(conn, first["mark_id"])
    assert old_mark["status"] == "superseded"
    assert old_mark["supersedes_mark_id"] == second["mark_id"]
