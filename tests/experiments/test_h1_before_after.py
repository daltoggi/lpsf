"""H1 before/after shift test."""

from lpsf.experiments.hypotheses.h1_before_after import build_scenario, verify
from lpsf.experiments.runner import run_experiment


def test_h1_lpsf_shifts_after_deepen(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    scenario = build_scenario(snapshot_id, event_id)
    result = run_experiment(
        conn,
        hypothesis_name="H1_before_after",
        scenario=scenario,
        baselines=["LLMOnly", "LLMPlusLPSF"],
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
        event_id=event_id,
        verify=verify,
    )
    assert result["passed"], result["failures"]

    lpsf_before = result["phase_results"]["before"]["LLMPlusLPSF"]
    lpsf_after = result["phase_results"]["after"]["LLMPlusLPSF"]
    assert lpsf_before.selected_path == "path:ev:A"
    assert lpsf_after.selected_path == "path:ev:B"

    llm_before = result["phase_results"]["before"]["LLMOnly"]
    llm_after = result["phase_results"]["after"]["LLMOnly"]
    assert llm_before.selected_path == llm_after.selected_path

    # active_marks must reference the deepen mark in the after phase
    assert any(m.startswith("mark_") for m in lpsf_after.active_marks)
