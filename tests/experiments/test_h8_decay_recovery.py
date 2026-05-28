"""H8 decay recovery: time-based natural weakening of an attractor.

Uses custom orchestration (not run_experiment) because apply_decay is not
a standard operator-dispatch member.
"""

from datetime import datetime

import pytest

from lpsf import db
from lpsf.experiments.baselines import LLMPlusLPSF, _load_attractors
from lpsf.experiments.hypotheses.h8_decay_recovery import (
    ELAPSED_HALF_LIVES,
    HALF_LIFE_SECONDS,
    INITIAL_DEPTH,
    build_rag_fixture,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG
from lpsf.experiments.scenarios import (
    insert_synthetic_event,
    insert_synthetic_snapshot,
)
from lpsf.operators.decay import apply_decay
from lpsf.operators.deepen_attractor import deepen_attractor


def _parse_iso(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


@pytest.fixture
def world():
    conn = db.init_db(":memory:")
    snap = insert_synthetic_snapshot(conn, snapshot_id="snap_h8")
    evt = insert_synthetic_event(conn, snapshot_id=snap, event_id="evt_h8")
    deepen_attractor(
        conn,
        event_id=evt,
        snapshot_id=snap,
        target_type="path",
        target_id="path:ev:B",
        strength=INITIAL_DEPTH,
        half_life=HALF_LIFE_SECONDS,
        evidence_refs=["ev:B"],
        reason="H8 initial bias",
        scope="h8",
    )
    rag = MockRAG(snapshot_id=snap, fixture=build_rag_fixture())
    llm = MockLLM(seed=0)
    yield conn, snap, evt, rag, llm
    conn.close()


def _select(conn, snap, rag, llm):
    baseline = LLMPlusLPSF()
    return baseline.respond(
        conn, query="tied query", snapshot_id=snap, llm=llm, rag=rag, seed=0
    )


def _last_activation_at(conn) -> int:
    row = conn.execute(
        "SELECT last_activation_at FROM attractors "
        "WHERE target_path = 'path:ev:B' AND snapshot_id = 'snap_h8'"
    ).fetchone()
    assert row is not None, "expected path:ev:B attractor to exist"
    return _parse_iso(row["last_activation_at"])


def test_h8_initial_bias_takes_hold(world):
    conn, snap, _, rag, llm = world
    resp = _select(conn, snap, rag, llm)
    assert resp.selected_path == "path:ev:B", (
        f"initial deepen should make B win; got {resp.selected_path} "
        f"(amplitudes={resp.amplitudes})"
    )


def test_h8_decay_reduces_effective_depth(world):
    """After 3 half-lives, _load_attractors should report depth ≈ 0.5^3 * INITIAL."""
    conn, snap, _, _, _ = world
    base = _last_activation_at(conn)
    now = base + ELAPSED_HALF_LIVES * HALF_LIFE_SECONDS
    apply_decay(conn, now=now, snapshot_id=snap)
    attractors = _load_attractors(conn, snap)
    assert "path:ev:B" in attractors
    expected = INITIAL_DEPTH * (0.5 ** ELAPSED_HALF_LIVES)
    actual = attractors["path:ev:B"]["depth"]
    assert actual == pytest.approx(expected, abs=1e-3), (
        f"effective depth after decay should be ~{expected:.3f}, got {actual:.3f}"
    )


def test_h8_decay_flips_selection_back_to_a(world):
    """The whole point: time-driven decay weakens bias enough to flip selection."""
    conn, snap, _, rag, llm = world
    before = _select(conn, snap, rag, llm)
    assert before.selected_path == "path:ev:B"

    base = _last_activation_at(conn)
    now = base + ELAPSED_HALF_LIVES * HALF_LIFE_SECONDS
    apply_decay(conn, now=now, snapshot_id=snap)

    after = _select(conn, snap, rag, llm)
    assert after.selected_path != "path:ev:B", (
        f"after {ELAPSED_HALF_LIVES} half-lives the bias should have decayed; "
        f"still selecting {after.selected_path} (amplitudes={after.amplitudes})"
    )


def test_h8_decay_with_one_half_life_only_partially_weakens(world):
    """Sanity: one half-life of decay shrinks depth ~50%, may or may not flip
    depending on dict ordering tiebreak; we only assert the depth is reduced."""
    conn, snap, _, _, _ = world
    base = _last_activation_at(conn)
    now = base + HALF_LIFE_SECONDS  # 1 half-life
    apply_decay(conn, now=now, snapshot_id=snap)
    attractors = _load_attractors(conn, snap)
    expected = INITIAL_DEPTH * 0.5
    actual = attractors["path:ev:B"]["depth"]
    assert actual == pytest.approx(expected, abs=1e-3), (
        f"after 1 half-life expected ~{expected}, got {actual}"
    )


def test_h8_without_decay_bias_persists(world):
    """Negative control: skipping apply_decay leaves the bias in place."""
    conn, snap, _, rag, llm = world
    r1 = _select(conn, snap, rag, llm)
    r2 = _select(conn, snap, rag, llm)
    assert r1.selected_path == r2.selected_path == "path:ev:B"
