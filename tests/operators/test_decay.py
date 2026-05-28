import json

from lpsf.operators.decay import apply_decay


def test_apply_decay_appends_decayed_rows_without_deleting_originals(conn, snapshot_id):
    conn.execute(
        """
        INSERT INTO attractors (
            target_path, depth, activation_threshold, half_life, last_activation_at,
            source_marks, decay_state, snapshot_id, created_at, updated_at
        )
        VALUES ('path:decay', 0.8, 0.4, '100', '1000', '["mark:a"]',
                '{"remaining":1.0}', ?, '1000', '1000')
        """,
        (snapshot_id,),
    )
    conn.execute(
        """
        INSERT INTO value_field_weights (
            axis_name, scope, weight, source_marks, decay_state,
            score_contribution_meta, snapshot_id, created_at, updated_at
        )
        VALUES ('source_grounding', 'project', 0.8, '["mark:v"]',
                '{"half_life":100,"remaining":1.0}', '{}', ?, '1000', '1000')
        """,
        (snapshot_id,),
    )
    conn.execute(
        """
        INSERT INTO sensitivity_profiles (
            profile_id, trigger_pattern, gain, threshold, scope, hard_policy,
            false_positive_observations, source_marks, decay_state, snapshot_id,
            created_at, updated_at
        )
        VALUES ('profile:decay', 'trigger', 1.8, 0.8, 'project', 0, '[]',
                '["mark:s"]', '{"half_life":100,"remaining":1.0}', ?,
                '1000', '1000')
        """,
        (snapshot_id,),
    )

    result = apply_decay(conn, now=1200, snapshot_id=snapshot_id)

    assert result["processed"] == {
        "attractors": 1,
        "value_field_weights": 1,
        "sensitivity_profiles": 1,
    }
    assert conn.execute("SELECT COUNT(*) FROM attractors").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM value_field_weights").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM sensitivity_profiles").fetchone()[0] == 2

    decayed = conn.execute(
        "SELECT * FROM attractors WHERE target_path != 'path:decay'"
    ).fetchone()
    assert round(decayed["depth"], 3) == 0.2
    assert json.loads(decayed["decay_state"])["decay_factor"] == 0.25
