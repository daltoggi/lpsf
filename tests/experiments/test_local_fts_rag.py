"""Tests for LocalFTSRag — real SQLite FTS5 RAG adapter."""

import sqlite3
from pathlib import Path

import pytest

from lpsf.experiments.local_fts_rag import LocalFTSRag, _bm25_to_score


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DB = REPO_ROOT / "data" / "corpus.fts.db"


@pytest.fixture
def db_path():
    if not CORPUS_DB.exists():
        pytest.skip(f"corpus FTS index missing at {CORPUS_DB}; run scripts/build_corpus.py")
    return str(CORPUS_DB)


def test_bm25_score_mapping_monotonic():
    # Smaller (more negative) bm25 → higher score
    assert _bm25_to_score(0.0) == 0.0
    s1 = _bm25_to_score(-1.0)
    s2 = _bm25_to_score(-2.0)
    s3 = _bm25_to_score(-10.0)
    assert 0 < s1 < s2 < s3 < 1.0


def test_retrieve_returns_candidates_for_relevant_query(db_path):
    rag = LocalFTSRag(db_path=db_path)
    results = rag.retrieve("SQLite database")
    assert len(results) >= 1
    # SQLite-related note should be top result
    assert "sqlite" in results[0]["id"].lower()


def test_retrieve_results_sorted_by_score_desc(db_path):
    rag = LocalFTSRag(db_path=db_path)
    results = rag.retrieve("search ranking retrieval")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), f"not sorted: {scores}"


def test_retrieve_shape_matches_mockrag(db_path):
    rag = LocalFTSRag(db_path=db_path)
    results = rag.retrieve("local-first software")
    for r in results:
        assert set(r.keys()) == {"id", "score", "sanitized_summary", "source_type"}
        assert isinstance(r["id"], str)
        assert isinstance(r["score"], float)
        assert 0.0 <= r["score"] <= 1.0
        assert isinstance(r["sanitized_summary"], str)
        assert r["source_type"] == "markdown"


def test_retrieve_never_returns_body(db_path):
    """Critical safety: raw body must NEVER appear in the output."""
    rag = LocalFTSRag(db_path=db_path)
    # Each note's body is ~500-1500 chars; summary is <= 280 chars.
    # If we accidentally returned body, summary len would exceed 280.
    results = rag.retrieve("database")
    for r in results:
        assert len(r["sanitized_summary"]) <= 280, (
            f"summary too long ({len(r['sanitized_summary'])} chars); "
            f"body may have leaked: {r['sanitized_summary'][:100]!r}..."
        )
        assert "body" not in r
        assert "body_length" not in r


def test_retrieve_empty_query_returns_empty(db_path):
    rag = LocalFTSRag(db_path=db_path)
    assert rag.retrieve("") == []
    assert rag.retrieve("   ") == []


def test_retrieve_punctuation_only_returns_empty(db_path):
    rag = LocalFTSRag(db_path=db_path)
    assert rag.retrieve("!!!") == []
    assert rag.retrieve(",.;:") == []


def test_retrieve_honors_limit(db_path):
    rag = LocalFTSRag(db_path=db_path)
    results = rag.retrieve("data", limit=2)
    assert len(results) <= 2


def test_read_only_mode_blocks_writes(db_path):
    """Connection is read-only; attempting to write must fail."""
    rag = LocalFTSRag(db_path=db_path)
    rag.retrieve("warm up connection")
    with pytest.raises(sqlite3.OperationalError):
        rag._conn.execute("INSERT INTO meta (id) VALUES ('attack')")


def test_missing_db_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="FTS index not found"):
        LocalFTSRag(db_path=str(tmp_path / "nonexistent.db"))


def test_drop_in_for_mockrag_in_baseline(db_path):
    """LocalFTSRag must work as a drop-in for MockRAG in LLMPlusRAG."""
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusRAG
    from lpsf.experiments.mock_llm import MockLLM
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )

    conn = db.init_db(":memory:")
    try:
        insert_synthetic_snapshot(conn, snapshot_id="snap_fts")
        insert_synthetic_event(conn, snapshot_id="snap_fts", event_id="evt_fts")
        rag = LocalFTSRag(db_path=db_path, snapshot_id="snap_fts")
        baseline = LLMPlusRAG()
        resp = baseline.respond(
            conn,
            query="reranking and retrieval",
            snapshot_id="snap_fts",
            llm=MockLLM(seed=0),
            rag=rag,
            seed=0,
        )
        assert resp.selected_path.startswith("path:")
        assert resp.evidence_refs  # at least one evidence ref came back
        assert resp.baseline_name == "LLMPlusRAG"
    finally:
        conn.close()


def test_close_releases_connection(db_path):
    rag = LocalFTSRag(db_path=db_path)
    rag.retrieve("test")
    assert rag._conn is not None
    rag.close()
    assert rag._conn is None
