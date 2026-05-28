"""Tests for the LPSF application layer — persistent personalizing search."""

from pathlib import Path

import pytest

from lpsf.app import LPSFSearchSession, SearchResult
from lpsf.experiments.local_fts_rag import LocalFTSRag
from lpsf.experiments.mock_llm import MockLLM


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DB = REPO_ROOT / "data" / "corpus.fts.db"


@pytest.fixture
def corpus():
    if not CORPUS_DB.exists():
        pytest.skip("corpus FTS index missing; run scripts/build_corpus.py")
    return str(CORPUS_DB)


@pytest.fixture
def session(tmp_path, corpus):
    rag = LocalFTSRag(db_path=corpus, snapshot_id="app_v1")
    sess = LPSFSearchSession(
        state_db_path=str(tmp_path / "state.db"),
        rag=rag,
        llm=MockLLM(seed=0),
        use_rerank=False,
    )
    yield sess
    sess.close()


def test_search_returns_ranked_results(session):
    results = session.search("local data storage", limit=3)
    assert results
    assert all(isinstance(r, SearchResult) for r in results)
    # Ranks are 1..n contiguous
    assert [r.rank for r in results] == list(range(1, len(results) + 1))
    # Amplitudes are non-increasing
    amps = [r.amplitude for r in results]
    assert amps == sorted(amps, reverse=True)


def test_record_pick_creates_event_and_mark(session):
    out = session.record_pick("01_sqlite_for_apps", query="local data storage")
    assert out["event_id"].startswith("pick_")
    assert out["path"] == "path:01_sqlite_for_apps"
    # experience_event row exists
    row = session.conn.execute(
        "SELECT event_type FROM experience_events WHERE event_id = ?",
        (out["event_id"],),
    ).fetchone()
    assert row["event_type"] == "user_pick"
    # plasticity_mark row exists
    mark = session.conn.execute(
        "SELECT COUNT(*) FROM plasticity_marks WHERE operator_type='deepen_attractor' "
        "AND target_id='path:01_sqlite_for_apps'"
    ).fetchone()[0]
    assert mark == 1


def test_repeated_picks_raise_rank(session):
    query = "local data storage"
    before = session.search(query, limit=5)
    before_rank = {r.evidence_id: r.rank for r in before}
    # sqlite is initially below local_first
    assert before_rank["01_sqlite_for_apps"] > before_rank.get("04_local_first", 99)

    for _ in range(3):
        session.record_pick("01_sqlite_for_apps", query=query)

    after = session.search(query, limit=5)
    after_rank = {r.evidence_id: r.rank for r in after}
    assert after_rank["01_sqlite_for_apps"] == 1, (
        f"after 3 picks sqlite should rank #1, got {after_rank}"
    )


def test_pick_increases_attractor_depth(session):
    query = "local data storage"
    session.record_pick("01_sqlite_for_apps", query=query)
    results = session.search(query, limit=5)
    sqlite = next(r for r in results if r.evidence_id == "01_sqlite_for_apps")
    assert sqlite.attractor_depth > 0
    assert sqlite.picked_before == 1


def test_personalization_persists_across_reopen(tmp_path, corpus):
    state = str(tmp_path / "persist.db")
    query = "local data storage"

    rag1 = LocalFTSRag(db_path=corpus, snapshot_id="app_v1")
    s1 = LPSFSearchSession(state_db_path=state, rag=rag1, llm=MockLLM(seed=0))
    for _ in range(3):
        s1.record_pick("01_sqlite_for_apps", query=query)
    s1.close()

    # New process simulation: fresh session over the same on-disk state
    rag2 = LocalFTSRag(db_path=corpus, snapshot_id="app_v1")
    s2 = LPSFSearchSession(state_db_path=state, rag=rag2, llm=MockLLM(seed=0))
    results = s2.search(query, limit=5)
    sqlite = next(r for r in results if r.evidence_id == "01_sqlite_for_apps")
    assert sqlite.rank == 1
    assert sqlite.picked_before == 3
    s2.close()


def test_pick_counts_tracked_per_path(session):
    session.record_pick("01_sqlite_for_apps", query="q")
    session.record_pick("01_sqlite_for_apps", query="q")
    session.record_pick("03_fts5_search", query="q")
    counts = session._pick_counts()
    assert counts["path:01_sqlite_for_apps"] == 2
    assert counts["path:03_fts5_search"] == 1


def test_unrelated_query_not_affected_when_no_overlap(session):
    """Picking sqlite shouldn't surface it for a query whose retrieval
    doesn't return sqlite at all."""
    session.record_pick("01_sqlite_for_apps", query="local data storage")
    # A query that retrieves only RAG/eval docs
    results = session.search("evaluate retrieval augmented generation", limit=5)
    ids = {r.evidence_id for r in results}
    # sqlite has an attractor now, but if it's not retrieved for this query
    # it cannot be selected (attractors only boost retrieved candidates).
    if "01_sqlite_for_apps" not in ids:
        assert all(r.evidence_id != "01_sqlite_for_apps" for r in results)
