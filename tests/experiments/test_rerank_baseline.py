"""Tests for LLMPlusLPSFRerank baseline (Phase D).

The new baseline introduces an LLM-derived ranking term into selection:
    amplitudes[c] = α·rag_score(c) + β·llm_rank(c) + γ·attractor_depth(c)

Unlike LLMPlusLPSF, the LLM response CAN affect selected_path here.
"""

import pytest

from lpsf import db
from lpsf.experiments.baselines import (
    LLMPlusLPSF,
    LLMPlusLPSFRerank,
    _parse_pair_choice,
    _pairwise_rank_scores,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG
from lpsf.experiments.scenarios import (
    insert_synthetic_event,
    insert_synthetic_snapshot,
)


@pytest.fixture
def conn():
    c = db.init_db(":memory:")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def snap_evt(conn):
    snap = insert_synthetic_snapshot(conn, snapshot_id="snap_rerank")
    evt = insert_synthetic_event(conn, snapshot_id=snap, event_id="evt_rerank")
    return snap, evt


class _ScriptedLLM:
    """LLM whose responses are dictated by the pair being asked about."""

    def __init__(self, choice: str = "A"):
        self.choice = choice
        self.calls = []

    def complete(self, prompt, *, context=None):
        self.calls.append(context)
        return {
            "response": self.choice,
            "confidence": 0.9,
            "evidence_refs": [],
            "model": self.version(),
        }

    def version(self):
        return "scripted-llm-v0"


# ---------- _parse_pair_choice --------------------------------------------

@pytest.mark.parametrize("response,expected", [
    ("A", "A"),
    ("B", "B"),
    ("a", "A"),
    ("b", "B"),
    ("  A  ", "A"),
    ("A: candidate A is more relevant", "A"),
    ("I pick B because...", "B"),
    ("", None),
    ("garbage", None),
])
def test_parse_pair_choice(response, expected):
    assert _parse_pair_choice(response) == expected


# ---------- _pairwise_rank_scores -----------------------------------------

def test_pairwise_returns_score_per_candidate():
    evidence = [
        {"id": "X", "score": 0.5, "sanitized_summary": "x"},
        {"id": "Y", "score": 0.5, "sanitized_summary": "y"},
    ]
    llm = _ScriptedLLM(choice="A")  # always picks the first (X)
    scores = _pairwise_rank_scores("q", evidence, llm)
    assert scores["path:X"] == 1.0
    assert scores["path:Y"] == 0.0


def test_pairwise_three_candidates_partial_winner():
    evidence = [
        {"id": "X", "score": 0.5, "sanitized_summary": "x"},
        {"id": "Y", "score": 0.5, "sanitized_summary": "y"},
        {"id": "Z", "score": 0.5, "sanitized_summary": "z"},
    ]
    llm = _ScriptedLLM(choice="A")  # always first → X beats Y, X beats Z, Y beats Z
    scores = _pairwise_rank_scores("q", evidence, llm)
    # X appeared in 2 pairs, won both → 1.0
    # Y appeared in 2 pairs, won 1 (vs Z) → 0.5
    # Z appeared in 2 pairs, won 0 → 0.0
    assert scores["path:X"] == pytest.approx(1.0)
    assert scores["path:Y"] == pytest.approx(0.5)
    assert scores["path:Z"] == pytest.approx(0.0)


def test_pairwise_single_candidate_returns_one():
    evidence = [{"id": "only", "score": 0.5, "sanitized_summary": "only"}]
    scores = _pairwise_rank_scores("q", evidence, _ScriptedLLM("A"))
    assert scores == {"path:only": 1.0}


# ---------- LLMPlusLPSFRerank behavior ------------------------------------

@pytest.fixture
def tied_rag(snap_evt):
    snap, _ = snap_evt
    return MockRAG(
        snapshot_id=snap,
        fixture={
            "best path": [
                {"id": "A", "score": 0.50, "sanitized_summary": "a"},
                {"id": "B", "score": 0.50, "sanitized_summary": "b"},
            ],
        },
    )


def test_rerank_llm_vote_breaks_tie(conn, snap_evt, tied_rag):
    """With α=γ=0 and tied RAG scores, the LLM vote alone decides."""
    snap, _ = snap_evt
    llm = _ScriptedLLM(choice="B")  # vote B
    baseline = LLMPlusLPSFRerank(alpha=0.0, beta=1.0, gamma=0.0)
    resp = baseline.respond(conn, query="best path", snapshot_id=snap, llm=llm, rag=tied_rag)
    assert resp.selected_path == "path:B"


def test_rerank_attractor_overrides_llm_vote(conn, snap_evt, tied_rag):
    """If LLM picks A but attractor on B is strong enough, B wins."""
    snap, _ = snap_evt
    from lpsf.operators.deepen_attractor import deepen_attractor
    deepen_attractor(
        conn,
        event_id="evt_rerank",
        snapshot_id=snap,
        target_type="path",
        target_id="path:B",
        strength=0.9,
        half_life=3600,
        evidence_refs=["B"],
        reason="test",
        scope="t",
    )
    llm = _ScriptedLLM(choice="A")  # LLM votes A
    baseline = LLMPlusLPSFRerank(alpha=0.0, beta=1.0, gamma=1.0)
    # amplitudes: A = 0 + 1*1 + 1*0 = 1.0; B = 0 + 1*0 + 1*0.9 = 0.9
    # A still wins because LLM vote (1.0) > attractor (0.9) when β=γ=1
    resp = baseline.respond(conn, query="best path", snapshot_id=snap, llm=llm, rag=tied_rag)
    assert resp.selected_path == "path:A", f"got {resp.selected_path}, amplitudes={resp.amplitudes}"

    # Now amplify the attractor weight
    baseline2 = LLMPlusLPSFRerank(alpha=0.0, beta=1.0, gamma=2.0)
    # amplitudes: A = 1.0; B = 2*0.9 = 1.8 → B wins
    resp2 = baseline2.respond(conn, query="best path", snapshot_id=snap, llm=llm, rag=tied_rag)
    assert resp2.selected_path == "path:B", f"got {resp2.selected_path}, amplitudes={resp2.amplitudes}"


def test_rerank_with_beta_zero_matches_lpsf(conn, snap_evt, tied_rag):
    """β=0 should make LLMPlusLPSFRerank equivalent to LLMPlusLPSF (modulo
    score_components metadata). selected_path must match."""
    snap, _ = snap_evt
    from lpsf.operators.deepen_attractor import deepen_attractor
    deepen_attractor(
        conn,
        event_id="evt_rerank",
        snapshot_id=snap,
        target_type="path",
        target_id="path:B",
        strength=0.3,
        half_life=3600,
        evidence_refs=["B"],
        reason="test",
        scope="t",
    )
    llm = _ScriptedLLM(choice="A")
    lpsf = LLMPlusLPSF()
    rerank = LLMPlusLPSFRerank(alpha=1.0, beta=0.0, gamma=1.0)
    r1 = lpsf.respond(conn, query="best path", snapshot_id=snap, llm=llm, rag=tied_rag)
    r2 = rerank.respond(conn, query="best path", snapshot_id=snap, llm=llm, rag=tied_rag)
    assert r1.selected_path == r2.selected_path


def test_rerank_baseline_registered():
    from lpsf.experiments.baselines import baseline_names, get_baseline
    assert "LLMPlusLPSFRerank" in baseline_names()
    inst = get_baseline("LLMPlusLPSFRerank")
    assert isinstance(inst, LLMPlusLPSFRerank)
