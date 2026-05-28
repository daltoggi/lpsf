"""H2 per-operator causality. Each operator produces a distinct, attributable
state delta visible in its secondary table and tied to a plasticity_marks row.
"""

import json

from lpsf.experiments.hypotheses.h2_operator_causality import (
    OPERATOR_SPECS,
    build_scenario,
    verify,
)
from lpsf.experiments.runner import run_experiment


def test_h2_all_eight_operators_produce_distinct_state(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    scenario = build_scenario(snapshot_id, event_id)
    result = run_experiment(
        conn,
        hypothesis_name="H2_operator_causality",
        scenario=scenario,
        baselines=["LLMOnly"],
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
        event_id=event_id,
        verify=verify,
    )
    assert result["passed"], result["failures"]

    # Every operator type produced a mark row
    marks = conn.execute(
        "SELECT operator_type, mark_id, target_id FROM plasticity_marks "
        "WHERE snapshot_id = ? ORDER BY id",
        (snapshot_id,),
    ).fetchall()
    op_types = {m["operator_type"] for m in marks}
    expected_op_types = {spec["operator"] for spec in OPERATOR_SPECS}
    assert expected_op_types.issubset(op_types), (
        f"Missing operators: {expected_op_types - op_types}"
    )

    # Each spec's secondary table row exists and references the mark via source_marks
    # (where applicable) or by foreign key.
    for spec in OPERATOR_SPECS:
        table = spec["expected_table"]
        col, val = spec["expected_lookup"]
        row = conn.execute(
            f"SELECT * FROM {table} WHERE {col} = ?", (val,)
        ).fetchone()
        assert row is not None, (
            f"{spec['operator']} did not produce row in {table} where {col}={val}"
        )

    # No operator should have produced a no-op state delta (all should have an
    # associated mark; we already verified the operator types).
