"""H4 snapshot reproducibility: same scenario + same seed -> identical outputs
across independent fresh DBs.
"""

from lpsf import db
from lpsf.experiments.hypotheses.h4_snapshot_reproducibility import (
    build_scenario,
    verify,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG
from lpsf.experiments.runner import run_experiment
from lpsf.experiments.scenarios import (
    default_rag_fixture,
    insert_synthetic_event,
    insert_synthetic_snapshot,
)


def _run_once(seed: int):
    conn = db.init_db(":memory:")
    snapshot_id = insert_synthetic_snapshot(conn, snapshot_id="snap_h4")
    event_id = insert_synthetic_event(
        conn, snapshot_id=snapshot_id, event_id="evt_h4"
    )
    fixture = default_rag_fixture()
    llm = MockLLM(seed=seed)
    rag = MockRAG(snapshot_id=snapshot_id, fixture=fixture)
    scenario = build_scenario(snapshot_id, event_id)
    result = run_experiment(
        conn,
        hypothesis_name="H4_snapshot_reproducibility",
        scenario=scenario,
        baselines=["LLMPlusLPSF"],
        snapshot_id=snapshot_id,
        llm=llm,
        rag=rag,
        event_id=event_id,
        seed=seed,
        verify=verify,
    )
    conn.close()
    return result


def test_h4_two_independent_runs_match():
    a = _run_once(seed=42)
    b = _run_once(seed=42)
    assert a["passed"]
    assert b["passed"]

    resp_a = a["phase_results"]["main"]["LLMPlusLPSF"]
    resp_b = b["phase_results"]["main"]["LLMPlusLPSF"]

    assert resp_a.selected_path == resp_b.selected_path
    assert resp_a.evidence_refs == resp_b.evidence_refs
    assert resp_a.active_attractors == resp_b.active_attractors
    assert resp_a.active_marks == resp_b.active_marks
    assert resp_a.amplitudes == resp_b.amplitudes


def test_h4_different_seed_can_differ_in_llm_path_only():
    a = _run_once(seed=1)
    b = _run_once(seed=2)
    resp_a = a["phase_results"]["main"]["LLMPlusLPSF"]
    resp_b = b["phase_results"]["main"]["LLMPlusLPSF"]
    # With marks dominating, selected_path is still expected to match the
    # attractor target regardless of seed.
    assert resp_a.selected_path == "path:ev:M1"
    assert resp_b.selected_path == "path:ev:M1"
