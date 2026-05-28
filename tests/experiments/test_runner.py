"""Tests for run_query and run_experiment orchestration + trace persistence."""

import json

from lpsf.experiments.runner import run_experiment, run_query


def test_run_query_writes_both_traces(conn, snapshot_id, mock_llm, mock_rag):
    out = run_query(
        conn,
        query="best path?",
        query_id="q_test_1",
        snapshot_id=snapshot_id,
        baseline_name="LLMPlusRAG",
        llm=mock_llm,
        rag=mock_rag,
    )
    assert out["hypothesis_trace_id"].startswith("htrace_")
    assert out["collapse_trace_id"].startswith("ctrace_")

    htrace = conn.execute(
        "SELECT * FROM hypothesis_traces WHERE trace_id = ?",
        (out["hypothesis_trace_id"],),
    ).fetchone()
    assert htrace is not None
    assert htrace["query_id"] == "q_test_1"
    assert htrace["snapshot_id"] == snapshot_id
    assert json.loads(htrace["candidates"])  # non-empty

    ctrace = conn.execute(
        "SELECT * FROM collapse_traces WHERE trace_id = ?",
        (out["collapse_trace_id"],),
    ).fetchone()
    assert ctrace is not None
    assert ctrace["selected_path"] == out["response"].selected_path


def test_run_query_score_components_populated(
    conn, snapshot_id, mock_llm, mock_rag
):
    out = run_query(
        conn,
        query="best path?",
        query_id="q_score",
        snapshot_id=snapshot_id,
        baseline_name="LLMPlusRAG",
        llm=mock_llm,
        rag=mock_rag,
        expected_keywords=["path"],
        available_evidence_ids=["ev:A", "ev:B"],
        active_attractor_paths=["path:ev:A"],
        forbidden_patterns=[],
    )
    sc = out["response"].score_components
    assert set(sc) == {
        "relevance",
        "evidence_grounding",
        "attractor_alignment",
        "sensitivity_compliance",
    }


def test_run_experiment_writes_evaluation_run(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    scenario = {
        "queries": [
            {"phase": "main", "query": "best path?", "query_id": "rt_q"},
        ],
        "operations": [],
        "scoring": {
            "expected_keywords": ["path"],
            "available_evidence_ids": ["ev:A", "ev:B"],
        },
    }
    result = run_experiment(
        conn,
        hypothesis_name="test_exp",
        scenario=scenario,
        baselines=["LLMOnly", "LLMPlusRAG"],
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
        event_id=event_id,
    )
    assert result["run_id"].startswith("run_")
    row = conn.execute(
        "SELECT * FROM evaluation_runs WHERE run_id = ?", (result["run_id"],)
    ).fetchone()
    assert row is not None
    assert row["suite_name"] == "test_exp"


def test_run_experiment_applies_operations(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    scenario = {
        "queries": [],
        "operations": [
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:A",
                    "strength": 0.5,
                    "half_life": 3600,
                    "evidence_refs": ["ev:A"],
                    "reason": "runner test",
                    "scope": "global",
                },
            },
        ],
        "scoring": {},
    }
    run_experiment(
        conn,
        hypothesis_name="runner_op_test",
        scenario=scenario,
        baselines=["LLMOnly"],
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
        event_id=event_id,
    )
    # Attractor row must exist
    row = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ? AND snapshot_id = ?",
        ("path:ev:A", snapshot_id),
    ).fetchone()
    assert row is not None
    assert float(row["depth"]) > 0
