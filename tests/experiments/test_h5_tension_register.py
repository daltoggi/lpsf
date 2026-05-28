"""H5 tension register: contradictory marks surface as unresolved_tensions."""

from lpsf.experiments.hypotheses.h5_tension_register import build_scenario, verify
from lpsf.experiments.runner import run_experiment


def test_h5_deepen_plus_inhibit_creates_tension(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    scenario = build_scenario(snapshot_id, event_id)
    result = run_experiment(
        conn,
        hypothesis_name="H5_tension_register",
        scenario=scenario,
        baselines=["LLMPlusLPSF"],
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
        event_id=event_id,
        verify=verify,
    )
    assert result["passed"], result["failures"]

    lpsf = result["phase_results"]["main"]["LLMPlusLPSF"]
    assert lpsf.unresolved_tensions
    tension = lpsf.unresolved_tensions[0]
    assert tension["candidate"] == "path:ev:X"
    assert tension["supporting_marks"]
    assert tension["inhibiting_marks"]
    assert any("priority guard" in w for w in lpsf.warnings)
