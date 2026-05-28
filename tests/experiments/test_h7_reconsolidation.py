"""H7 reconsolidation: deepened bias can be reversed by counter-experience."""

import pytest

from lpsf import db
from lpsf.experiments.hypotheses.h7_reconsolidation import (
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
    snap = insert_synthetic_snapshot(conn, snapshot_id="snap_h7")
    evt = insert_synthetic_event(conn, snapshot_id=snap, event_id="evt_h7")
    fixture = build_rag_fixture()
    rag = MockRAG(snapshot_id=snap, fixture=fixture)
    llm = MockLLM(seed=0)
    scenario = build_scenario(snap, evt)
    scenario.pop("_rag_fixture", None)
    return conn, snap, evt, rag, llm, scenario


def _run(world):
    conn, snap, evt, rag, llm, scenario = world
    return run_experiment(
        conn,
        hypothesis_name="H7_reconsolidation",
        scenario=scenario,
        baselines=("LLMPlusLPSF",),
        snapshot_id=snap,
        llm=llm,
        rag=rag,
        event_id=evt,
        seed=0,
        verify=verify,
    )


def test_h7_initial_bias_takes_hold(world):
    result = _run(world)
    initial = result["phase_results"]["initial"]["LLMPlusLPSF"]
    assert initial.selected_path == "path:ev:B", (
        f"initial deepen on B should make B win; got {initial.selected_path}"
    )


def test_h7_weaken_reverses_bias(world):
    result = _run(world)
    reversed_ = result["phase_results"]["reversed"]["LLMPlusLPSF"]
    assert reversed_.selected_path != "path:ev:B", (
        f"weaken should have reversed the bias; B still wins: {reversed_.selected_path}"
    )


def test_h7_competing_attractor_overrides(world):
    result = _run(world)
    overridden = result["phase_results"]["overridden"]["LLMPlusLPSF"]
    assert overridden.selected_path == "path:ev:A", (
        f"competing attractor on A should win; got {overridden.selected_path}"
    )


def test_h7_selected_path_changes_across_phases(world):
    result = _run(world)
    pr = result["phase_results"]
    paths = {
        pr["initial"]["LLMPlusLPSF"].selected_path,
        pr["reversed"]["LLMPlusLPSF"].selected_path,
        pr["overridden"]["LLMPlusLPSF"].selected_path,
    }
    assert len(paths) >= 2, f"plasticity check: selection never changed ({paths})"


def test_h7_passes_verify(world):
    result = _run(world)
    assert result["passed"], result["failures"]
