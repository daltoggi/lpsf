"""H3 privacy safety: synthetic sensitive body must never leak."""

import json

from lpsf.experiments.hypotheses.h3_privacy_safety import (
    SYNTHETIC_SENSITIVE_BODY,
    build_rag_fixture,
    build_scenario,
    verify,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG
from lpsf.experiments.runner import run_experiment


def test_h3_no_sensitive_leak_across_all_baselines(
    conn, snapshot_id, event_id
):
    fixture = build_rag_fixture()
    rag = MockRAG(snapshot_id=snapshot_id, fixture=fixture)
    llm = MockLLM(seed=0)
    scenario = build_scenario(snapshot_id, event_id)
    result = run_experiment(
        conn,
        hypothesis_name="H3_privacy_safety",
        scenario=scenario,
        baselines=["LLMOnly", "LLMPlusRAG", "LLMPlusStaticMemory", "LLMPlusLPSF"],
        snapshot_id=snapshot_id,
        llm=llm,
        rag=rag,
        event_id=event_id,
        verify=verify,
    )
    assert result["passed"], result["failures"]


def test_h3_traces_do_not_contain_sensitive_body(
    conn, snapshot_id, event_id
):
    fixture = build_rag_fixture()
    rag = MockRAG(snapshot_id=snapshot_id, fixture=fixture)
    llm = MockLLM(seed=0)
    scenario = build_scenario(snapshot_id, event_id)
    run_experiment(
        conn,
        hypothesis_name="H3_privacy_safety_traces",
        scenario=scenario,
        baselines=["LLMPlusLPSF"],
        snapshot_id=snapshot_id,
        llm=llm,
        rag=rag,
        event_id=event_id,
        verify=verify,
    )

    # Inspect every persisted trace/run row for leakage
    for table in ("hypothesis_traces", "collapse_traces", "evaluation_runs"):
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            for key in row.keys():
                value = row[key]
                if value is None:
                    continue
                assert SYNTHETIC_SENSITIVE_BODY not in str(value), (
                    f"H3 leak in {table}.{key}"
                )
