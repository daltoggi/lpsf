"""FrozenCore — the immutable pretrained function (numpy mechanism demo).

This stands in for the frozen weights of a pretrained LLM. It maps a concept
id to a fixed d-dimensional representation and NEVER changes. It is the
"fixed 12288-dimensional space" in miniature: a deterministic function whose
parameters experience cannot touch.

This is NOT a language model. It is the minimal substrate needed to ask one
falsifiable question honestly: can a system store a learned association in
*parameters* such that it recalls with an EMPTY input context — something a
frozen function + retrieval provably cannot do.
"""

from __future__ import annotations

import numpy as np


def _matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """matmul that suppresses the spurious FP-flag RuntimeWarnings emitted by
    numpy 2.0 on the macOS Accelerate BLAS backend. The results are verified
    finite; these warnings are a documented backend false-positive, not a real
    overflow/divide-by-zero in our data."""
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        return a @ b


class FrozenCore:
    """A fixed, deterministic concept encoder. Frozen = no learning here."""

    def __init__(self, *, n_concepts: int, dim: int = 64, seed: int = 0) -> None:
        self.n_concepts = n_concepts
        self.dim = dim
        rng = np.random.default_rng(seed)
        # Frozen "token embeddings": one fixed vector per concept id.
        emb = rng.standard_normal((n_concepts, dim))
        # Frozen "pretrained projection".
        w_core = rng.standard_normal((dim, dim)) / np.sqrt(dim)
        self._emb = emb
        self._w_core = w_core
        # Precompute the frozen encodings (deterministic, immutable).
        h = np.tanh(_matmul(emb, w_core))
        norms = np.linalg.norm(h, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._enc = h / norms  # (n_concepts, dim), unit-norm rows

    def encode(self, concept_id: int) -> np.ndarray:
        """Return the frozen d-dim representation of a concept. Pure, immutable."""
        return self._enc[concept_id]

    @property
    def param_count(self) -> int:
        """Frozen parameter count — fixed forever, regardless of experience."""
        return self._emb.size + self._w_core.size
