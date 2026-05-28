"""H6 adversarial scenario: LPSF overrides the best RAG candidate."""

import pytest

from lpsf import db
from lpsf.experiments.hypotheses.h6_adversarial import (
    build_rag_fixture,
    build_scenario,
    verify,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG
from lpsf.experiments.runner import run_experiment
from lpsf.experiments.scenarios import insert_synthetic_event, insert_synthetic_snapshot


@pytest.fixture
def conn():
    c = db.init_db(":memory:")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def world(conn):
    snap = insert_synthetic_snapshot(conn, snapshot_id="snap_h6")
    evt = insert_synthetic_event(conn, snapshot_id=snap, event_id="evt_h6")
    fixture = build_rag_fixture()
    rag = MockRAG(snapshot_id=snap, fixture=fixture)
    llm = MockLLM(seed=0)
    scenario = build_scenario(snap, evt)
    scenario.pop("_rag_fixture", None)
    return conn, snap, evt, rag, llm, scenario


def test_h6_lpsf_selects_wrong_path(world):
    conn, snap, evt, rag, llm, scenario = world
    result = run_experiment(
        conn,
        hypothesis_name="H6_adversarial",
        scenario=scenario,
        baselines=("LLMPlusRAG", "LLMPlusLPSF"),
        snapshot_id=snap,
        llm=llm,
        rag=rag,
        event_id=evt,
        seed=0,
        verify=verify,
    )
    main = result["phase_results"]["main"]
    assert main["LLMPlusLPSF"].selected_path == "path:ev:wrong", (
        f"LPSF should pick adversarial path, got {main['LLMPlusLPSF'].selected_path}"
    )


def test_h6_rag_selects_correct_path(world):
    conn, snap, evt, rag, llm, scenario = world
    result = run_experiment(
        conn,
        hypothesis_name="H6_adversarial",
        scenario=scenario,
        baselines=("LLMPlusRAG", "LLMPlusLPSF"),
        snapshot_id=snap,
        llm=llm,
        rag=rag,
        event_id=evt,
        seed=0,
        verify=verify,
    )
    main = result["phase_results"]["main"]
    assert main["LLMPlusRAG"].selected_path == "path:ev:correct", (
        f"RAG baseline should pick the highest-score path, got {main['LLMPlusRAG'].selected_path}"
    )


def test_h6_baselines_diverge(world):
    conn, snap, evt, rag, llm, scenario = world
    result = run_experiment(
        conn,
        hypothesis_name="H6_adversarial",
        scenario=scenario,
        baselines=("LLMPlusRAG", "LLMPlusLPSF"),
        snapshot_id=snap,
        llm=llm,
        rag=rag,
        event_id=evt,
        seed=0,
        verify=verify,
    )
    main = result["phase_results"]["main"]
    assert main["LLMPlusLPSF"].selected_path != main["LLMPlusRAG"].selected_path, (
        "H6 requires baselines to diverge"
    )


def test_h6_passes_verify(world):
    conn, snap, evt, rag, llm, scenario = world
    result = run_experiment(
        conn,
        hypothesis_name="H6_adversarial",
        scenario=scenario,
        baselines=("LLMPlusRAG", "LLMPlusLPSF"),
        snapshot_id=snap,
        llm=llm,
        rag=rag,
        event_id=evt,
        seed=0,
        verify=verify,
    )
    assert result["passed"], result["failures"]
