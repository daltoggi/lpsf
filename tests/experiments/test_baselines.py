"""Tests for the 4 experiment baselines."""

from lpsf.experiments.baselines import (
    LLMOnly,
    LLMPlusLPSF,
    LLMPlusRAG,
    LLMPlusStaticMemory,
    Response,
    baseline_names,
    get_baseline,
)


def test_baseline_names_complete():
    assert set(baseline_names()) == {
        "LLMOnly",
        "LLMPlusRAG",
        "LLMPlusStaticMemory",
        "LLMPlusLPSF",
        "LLMPlusLPSFRerank",
    }


def test_get_baseline_unknown_raises():
    import pytest
    with pytest.raises(KeyError):
        get_baseline("NonexistentBaseline")


def test_llm_only_no_rag(conn, snapshot_id, mock_llm):
    baseline = LLMOnly()
    resp = baseline.respond(
        conn,
        query="hello",
        snapshot_id=snapshot_id,
        llm=mock_llm,
    )
    assert isinstance(resp, Response)
    assert resp.baseline_name == "LLMOnly"
    assert resp.evidence_refs == []
    assert resp.active_attractors == []
    assert resp.active_marks == []
    assert resp.selected_path.startswith("path:llm:")


def test_llm_plus_rag_uses_rag(conn, snapshot_id, mock_llm, mock_rag):
    baseline = LLMPlusRAG()
    resp = baseline.respond(
        conn,
        query="best path?",
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
    )
    assert resp.baseline_name == "LLMPlusRAG"
    # RAG fixture returns ev:A and ev:B for "best path"
    assert set(resp.evidence_refs) == {"ev:A", "ev:B"}
    # Top scorer is ev:A (0.8)
    assert resp.selected_path == "path:ev:A"
    assert "path:ev:B" in resp.rejected_paths


def test_llm_plus_static_memory_hit(conn, snapshot_id, mock_llm):
    baseline = LLMPlusStaticMemory()
    resp = baseline.respond(
        conn,
        query="known query about topic",
        snapshot_id=snapshot_id,
        llm=mock_llm,
        static_memory={"known query": "path:static:preferred"},
    )
    assert resp.selected_path == "path:static:preferred"
    assert any("static_memory hit" in w for w in resp.warnings)


def test_llm_plus_static_memory_miss_falls_back_to_llm(
    conn, snapshot_id, mock_llm
):
    baseline = LLMPlusStaticMemory()
    resp = baseline.respond(
        conn,
        query="unknown query",
        snapshot_id=snapshot_id,
        llm=mock_llm,
        static_memory={"completely different pattern": "x"},
    )
    assert resp.selected_path.startswith("path:llm:")


def test_llm_plus_lpsf_with_no_marks_picks_top_rag(
    conn, snapshot_id, mock_llm, mock_rag
):
    baseline = LLMPlusLPSF()
    resp = baseline.respond(
        conn,
        query="best path?",
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
    )
    assert resp.baseline_name == "LLMPlusLPSF"
    assert resp.selected_path == "path:ev:A"  # highest base score
    assert resp.active_attractors == []
    assert resp.active_marks == []


def test_llm_plus_lpsf_attractor_shifts_selection(
    conn, snapshot_id, event_id, mock_llm, mock_rag
):
    from lpsf.operators import deepen_attractor

    # Deepen path:ev:B
    deepen_attractor(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="path",
        target_id="path:ev:B",
        strength=0.7,
        half_life=3600,
        evidence_refs=["ev:B"],
        reason="test",
        scope="global",
    )

    baseline = LLMPlusLPSF()
    resp = baseline.respond(
        conn,
        query="best path?",
        snapshot_id=snapshot_id,
        llm=mock_llm,
        rag=mock_rag,
    )
    assert resp.selected_path == "path:ev:B"
    assert "path:ev:B" in resp.active_attractors
    assert len(resp.active_marks) >= 1


def test_llm_plus_rag_requires_rag(conn, snapshot_id, mock_llm):
    import pytest
    baseline = LLMPlusRAG()
    with pytest.raises(ValueError):
        baseline.respond(conn, query="x", snapshot_id=snapshot_id, llm=mock_llm)


def test_llm_plus_lpsf_requires_rag(conn, snapshot_id, mock_llm):
    import pytest
    baseline = LLMPlusLPSF()
    with pytest.raises(ValueError):
        baseline.respond(conn, query="x", snapshot_id=snapshot_id, llm=mock_llm)
