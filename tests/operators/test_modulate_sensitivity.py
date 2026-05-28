from lpsf.operators import modulate_sensitivity

from tests.operators.conftest import fetch_mark, json_field


def test_modulate_sensitivity_inserts_profile_and_preserves_hard_policy(
    conn, event_id, snapshot_id, evidence_refs
):
    first = modulate_sensitivity(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        trigger_pattern="환각주의",
        gain=1.4,
        threshold=0.7,
        strength=0.4,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="increase source-grounding mode",
        scope="project",
        hard_policy=True,
    )
    second = modulate_sensitivity(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        trigger_pattern="환각주의",
        gain=1.1,
        threshold=0.5,
        strength=0.2,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="later softer sensitivity",
        scope="project",
        hard_policy=False,
    )

    row = conn.execute(
        "SELECT * FROM sensitivity_profiles WHERE trigger_pattern = '환각주의'"
    ).fetchone()
    assert row["gain"] == 1.1
    assert row["threshold"] == 0.5
    assert row["hard_policy"] == 1
    assert second["mark_id"] in json_field(dict(row), "source_marks")

    old_mark = fetch_mark(conn, first["mark_id"])
    assert old_mark["status"] == "superseded"
    assert old_mark["supersedes_mark_id"] == second["mark_id"]
