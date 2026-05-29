"""Tests for LoRAWeightMemory — LPSF operators in LoRA weight space."""

import math

import numpy as np
import pytest

from lpsf.substrate import FrozenCore
from lpsf.substrate.lora_memory import LoRAWeightMemory


def _value_embeddings(n, dim, seed=7):
    rng = np.random.default_rng(seed)
    v = rng.standard_normal((n, dim))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v


@pytest.fixture
def world():
    core = FrozenCore(n_concepts=20, dim=32, seed=0)
    mem = LoRAWeightMemory(d_in=32, d_out=32, rank=4, lr=0.3, seed=0)
    val_emb = _value_embeddings(20, 32, seed=7)
    return core, mem, val_emb


def test_deepen_improves_recall(world):
    core, mem, val_emb = world
    k = core.encode(5)
    v = val_emb[5]
    # Before any learning, recall is arbitrary.
    # After enough deepen steps, the correct value should win.
    for _ in range(10):
        mem.deepen(k, v, strength=1.0)
    pred = mem.recall(k, val_emb)
    assert pred == 5, f"after 10 deepen steps expected 5, got {pred}"


def test_weaken_reduces_alignment(world):
    core, mem, val_emb = world
    k = core.encode(3)
    v = val_emb[3]
    for _ in range(5):
        mem.deepen(k, v, strength=1.0)
    before = float(np.dot(mem.encode(k), v))
    mem.weaken(k, strength=0.8)
    after = float(np.dot(mem.encode(k), v))
    assert after < before, f"weaken should reduce alignment: {before:.3f} → {after:.3f}"


def test_decay_shrinks_weights(world):
    core, mem, val_emb = world
    k = core.encode(7)
    v = val_emb[7]
    for _ in range(5):
        mem.deepen(k, v, strength=1.0)
    norm_before = np.linalg.norm(mem._A) + np.linalg.norm(mem._B)
    factor = mem.decay(half_life=100, elapsed=100)  # 1 half-life → 0.5
    norm_after = np.linalg.norm(mem._A) + np.linalg.norm(mem._B)
    assert abs(factor - 0.5) < 1e-6
    assert norm_after < norm_before


def test_decay_factor_formula(world):
    _, mem, _ = world
    f1 = mem.decay(half_life=100, elapsed=200)  # 2 half-lives
    assert abs(f1 - 0.25) < 1e-6
    f2 = mem.decay(half_life=100, elapsed=0)    # 0 half-lives
    assert abs(f2 - 1.0) < 1e-6


def test_param_count_fixed(world):
    core, mem, val_emb = world
    p0 = mem.param_count
    for i in range(10):
        mem.deepen(core.encode(i), val_emb[i])
    assert mem.param_count == p0, "LoRA params are fixed even as facts are learned"


def test_marks_accumulate(world):
    core, mem, val_emb = world
    assert mem.n_marks == 0
    mem.deepen(core.encode(0), val_emb[0])
    mem.weaken(core.encode(0))
    assert mem.n_marks == 2


def test_decay_after_weaken_compounds(world):
    """weaken then decay should compound: both reduce the aligned component."""
    core, mem, val_emb = world
    k = core.encode(2)
    v = val_emb[2]
    for _ in range(8):
        mem.deepen(k, v, strength=1.0)
    alignment_full = float(np.dot(mem.encode(k), v))
    mem.weaken(k, strength=0.5)
    mem.decay(half_life=100, elapsed=100)
    alignment_reduced = float(np.dot(mem.encode(k), v))
    assert alignment_reduced < alignment_full
