from lpsf.operators import deepen_attractor, inhibit_path
from lpsf.operators.priority import ORDER


def test_priority_order_matches_m3_contract():
    assert ORDER == (
        "inhibit_path",
        "remap_schema",
        "reconsolidate_memory",
        "open_path",
        "deepen_attractor",
        "weaken_attractor",
        "tilt_value_field",
        "modulate_sensitivity",
    )


def test_lower_priority_operator_warns_and_does_not_override_active_inhibition(
    conn, event_id, snapshot_id, evidence_refs
):
    target_id = "path:forbidden"
    inhibit_path(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.9,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="forbidden path",
    )

    result = deepen_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id=target_id,
        strength=0.4,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="lower priority attempt",
    )

    assert result["warnings"]
    assert result["state_delta"]["blocked_by_priority"] is True
    attractor = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ?", (target_id,)
    ).fetchone()
    assert attractor["depth"] == 0
    assert attractor["activation_threshold"] == 1
