from lpsf.operators import inhibit_path
from lpsf.operators._base import priority_check

from tests.operators.conftest import fetch_mark, json_field


def test_inhibit_path_creates_high_priority_inhibition_marker(
    conn, event_id, snapshot_id, evidence_refs
):
    target_id = "path:raw-private-export"
    result = inhibit_path(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.9,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="hard privacy boundary",
    )

    mark = fetch_mark(conn, result["mark_id"])
    assert mark["operator_type"] == "inhibit_path"
    assert mark["status"] == "active"

    attractor = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ?", (target_id,)
    ).fetchone()
    assert attractor["depth"] == 0
    assert attractor["activation_threshold"] == 1
    assert json_field(dict(attractor), "decay_state")["inhibition_strength"] == 0.9

    warnings = priority_check("deepen_attractor", [mark])
    assert warnings
    assert "higher-priority inhibit_path" in warnings[0]
