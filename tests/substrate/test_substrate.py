"""Tests for the substrate track — the falsifiable memory-in-parameters claim."""

import warnings

import numpy as np
import pytest

from lpsf.substrate import ExpandableMemory, FixedHebbian, FrozenCore, FrozenRAG


def _facts(n):
    return [(k, k) for k in range(n)]


def _empty_ctx_recall(mem, facts):
    return np.mean([mem.recall(k, context_value=None) == v for k, v in facts])


# ---- the core falsifiable test ------------------------------------------

def test_frozen_rag_fails_empty_context():
    """No parameters learned → empty-context recall is at chance."""
    core = FrozenCore(n_concepts=50, dim=48, seed=0)
    rag = FrozenRAG(core, 50, seed=0)
    facts = _facts(50)
    for k, v in facts:
        rag.learn(k, v)
    acc = _empty_ctx_recall(rag, facts)
    assert acc < 0.1, f"frozen RAG should be ~chance with empty context, got {acc}"


def test_frozen_rag_succeeds_with_context():
    """With the value in context it just copies → perfect. Proves it's memory,
    not capability, that's missing."""
    core = FrozenCore(n_concepts=10, dim=48, seed=0)
    rag = FrozenRAG(core, 10, seed=0)
    acc = np.mean([rag.recall(k, context_value=k) == k for k in range(10)])
    assert acc == 1.0


def test_expandable_recalls_with_empty_context():
    """Memory in (growing) parameters → recall works with NO context."""
    core = FrozenCore(n_concepts=80, dim=48, seed=0)
    mem = ExpandableMemory(core, 80)
    facts = _facts(80)
    for k, v in facts:
        mem.learn(k, v)
    acc = _empty_ctx_recall(mem, facts)
    assert acc == 1.0, f"expandable should recall all with empty context, got {acc}"


# ---- the fixed-dimension limit ------------------------------------------

def test_fixed_hebbian_forgets_beyond_capacity():
    """Fixed-size associative matrix degrades as facts exceed its dimension."""
    core = FrozenCore(n_concepts=120, dim=48, seed=0)

    mem_small = FixedHebbian(core, 120, seed=0)
    for k, v in _facts(20):
        mem_small.learn(k, v)
    acc_small = _empty_ctx_recall(mem_small, _facts(20))

    mem_big = FixedHebbian(core, 120, seed=0)
    for k, v in _facts(120):
        mem_big.learn(k, v)
    acc_big = _empty_ctx_recall(mem_big, _facts(120))

    assert acc_small > acc_big, (
        f"hebbian should forget at scale: {acc_small} (20 facts) vs {acc_big} (120)"
    )
    assert acc_big < 0.9, f"at 120 facts >> dim 48, expect clear forgetting, got {acc_big}"


def test_expandable_does_not_forget_at_scale():
    core = FrozenCore(n_concepts=120, dim=48, seed=0)
    mem = ExpandableMemory(core, 120)
    for k, v in _facts(120):
        mem.learn(k, v)
    assert _empty_ctx_recall(mem, _facts(120)) == 1.0


# ---- parameter growth (escaping the fixed dimension) --------------------

def test_param_growth_contrast():
    core = FrozenCore(n_concepts=100, dim=48, seed=0)
    heb = FixedHebbian(core, 100, seed=0)
    exp = ExpandableMemory(core, 100)

    heb_p0 = heb.param_count
    exp_p0 = exp.param_count
    for k, v in _facts(50):
        heb.learn(k, v)
        exp.learn(k, v)
    assert heb.param_count == heb_p0, "Hebbian params must stay FIXED"
    assert exp.param_count > exp_p0, "Expandable params must GROW with experience"
    assert exp.n_slots == 50


def test_frozen_core_is_immutable():
    core = FrozenCore(n_concepts=10, dim=32, seed=1)
    e1 = core.encode(3).copy()
    # learning in any memory must not change the core's encoding
    mem = ExpandableMemory(core, 10)
    for k in range(10):
        mem.learn(k, k)
    assert np.allclose(core.encode(3), e1)
    assert core.param_count > 0


# ---- determinism + cleanliness ------------------------------------------

def test_determinism():
    def run():
        core = FrozenCore(n_concepts=40, dim=48, seed=5)
        mem = ExpandableMemory(core, 40)
        for k, v in _facts(40):
            mem.learn(k, v)
        return [mem.recall(k) for k in range(40)]
    assert run() == run()


def test_no_runtime_warnings_emitted():
    """The macOS Accelerate matmul false-positives must be suppressed."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        core = FrozenCore(n_concepts=60, dim=48, seed=0)
        for cls in (lambda: FrozenRAG(core, 60, seed=0),
                    lambda: FixedHebbian(core, 60, seed=0),
                    lambda: ExpandableMemory(core, 60)):
            mem = cls()
            for k, v in _facts(60):
                mem.learn(k, v)
            for k in range(60):
                mem.recall(k, context_value=None)
