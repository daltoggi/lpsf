"""Three memory systems over a shared FrozenCore.

The falsifiable question: after learning facts (key -> value), can the system
recall the value for a key with an EMPTY input context? If yes, the memory
lives in parameters (true memory). If only-with-context, it's input
rearrangement (RAG / fixed-dimension search).

  1. FrozenRAG        — no learnable params. Recall needs the value in context.
                        Empty context => chance. (The hosted-API ceiling.)
  2. FixedHebbian     — one fixed d_val x d associative matrix, Hebbian writes.
                        Empty-context recall works early but SATURATES and
                        FORGETS as facts exceed its fixed capacity.
                        (The fixed-dimension limit.)
  3. ExpandableMemory — one parameter slot appended per fact. Empty-context
                        recall works AND capacity grows with experience, so it
                        does not forget. (Escaping the fixed dimension.)

All deterministic given seeds. numpy only.
"""

from __future__ import annotations

import numpy as np

from .core import FrozenCore, _matmul


def _value_embeddings(n_values: int, dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed + 7)
    v = rng.standard_normal((n_values, dim))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v


class FrozenRAG:
    """Frozen core + retrieval. No parameters are learned from experience.

    To answer, the value must be supplied in `context`. With empty context the
    system has only the frozen function, which knows nothing of the learned
    association -> chance accuracy. This is the honest stand-in for a hosted
    API where you cannot touch weights or activations.
    """

    name = "frozen_rag"

    def __init__(self, core: FrozenCore, n_values: int, seed: int = 0) -> None:
        self.core = core
        self.n_values = n_values
        rng = np.random.default_rng(seed + 3)
        # A fixed, uninformed readout: maps a concept encoding to a value guess
        # with NO knowledge of any learned key->value fact.
        self._w_out = rng.standard_normal((n_values, core.dim)) / np.sqrt(core.dim)

    def learn(self, key: int, value: int) -> None:
        # Nothing is stored in parameters. (A real RAG would index the fact in
        # an external store; here the "store" is simply the context passed at
        # recall time.)
        return None

    def recall(self, key: int, context_value: int | None = None) -> int:
        if context_value is not None:
            # With the value in context, the model just copies it.
            return context_value
        # Empty context: only the frozen, uninformed readout. ~chance.
        logits = _matmul(self._w_out, self.core.encode(key))
        return int(np.argmax(logits))

    @property
    def param_count(self) -> int:
        return 0  # learns nothing


class FixedHebbian:
    """A single fixed-size associative memory matrix, written by Hebbian rule.

    M (d_val x d) starts at zero. learn(key, value): M += outer(value_vec,
    enc(key)). recall: nearest value embedding to M @ enc(key). Capacity is
    bounded by the FIXED dimension -> as facts accumulate, crosstalk grows and
    older facts are overwritten (catastrophic interference). This is the
    "fixed 12288-dim" limit made small.
    """

    name = "fixed_hebbian"

    def __init__(self, core: FrozenCore, n_values: int, seed: int = 0) -> None:
        self.core = core
        self.n_values = n_values
        self._val_emb = _value_embeddings(n_values, core.dim, seed)
        self._M = np.zeros((core.dim, core.dim))

    def learn(self, key: int, value: int) -> None:
        k = self.core.encode(key)
        v = self._val_emb[value]
        self._M += np.outer(v, k)  # Hebbian outer-product write

    def recall(self, key: int, context_value: int | None = None) -> int:
        vhat = _matmul(self._M, self.core.encode(key))
        sims = _matmul(self._val_emb, vhat)
        return int(np.argmax(sims))

    @property
    def param_count(self) -> int:
        return self._M.size  # FIXED — does not grow with experience


class SparseHebbian:
    """Hebbian associative memory over a sparse k-winner-take-all code.

    Same FIXED-dimension regime as FixedHebbian, but stores associations over a
    sparse code (project to code_dim, keep the top-k magnitudes). Sparse codes
    are near-orthogonal, so crosstalk is far lower and effective capacity is
    much higher than dense Hebbian — yet still bounded and linear in the fixed
    code dimension. It raises the ceiling; it does not remove it.
    """

    name = "sparse_hebbian"

    def __init__(self, core: FrozenCore, n_values: int, *, code_dim: int = 256,
                 k: int = 8, seed: int = 0) -> None:
        self.core = core
        self.n_values = n_values
        self.code_dim = code_dim
        self.k = k
        rng = np.random.default_rng(seed + 11)
        self._P = rng.standard_normal((code_dim, core.dim)) / np.sqrt(core.dim)
        self._val_emb = _value_embeddings(n_values, code_dim, seed)
        self._M = np.zeros((code_dim, code_dim))

    def _code(self, key: int) -> np.ndarray:
        proj = _matmul(self._P, self.core.encode(key))
        kk = min(self.k, proj.size)
        idx = np.argpartition(np.abs(proj), -kk)[-kk:]
        code = np.zeros_like(proj)
        code[idx] = proj[idx]
        n = np.linalg.norm(code)
        return code / n if n > 0 else code

    def learn(self, key: int, value: int) -> None:
        c = self._code(key)
        self._M += np.outer(self._val_emb[value], c)

    def recall(self, key: int, context_value: int | None = None) -> int:
        vhat = _matmul(self._M, self._code(key))
        sims = _matmul(self._val_emb, vhat)
        return int(np.argmax(sims))

    @property
    def param_count(self) -> int:
        return self._M.size  # FIXED (code_dim^2)


class ExpandableMemory:
    """A growing key-value memory: one slot appended per (new) fact.

    learn(key, value): append slot (enc(key), value). If the key is already
    stored (near-duplicate prototype), update that slot instead of appending.
    recall: softmax attention over slot prototypes -> value vote. Capacity (and
    parameter count) GROWS with experience, so distinct facts never overwrite
    each other. This is the mechanism that escapes the fixed dimension.
    """

    name = "expandable"

    def __init__(self, core: FrozenCore, n_values: int, *, temp: float = 0.05,
                 merge_threshold: float = 0.999) -> None:
        self.core = core
        self.n_values = n_values
        self.temp = temp
        self.merge_threshold = merge_threshold
        self._protos: list[np.ndarray] = []
        self._values: list[int] = []

    def learn(self, key: int, value: int) -> None:
        k = self.core.encode(key)
        for i, p in enumerate(self._protos):
            if float(_matmul(p, k)) >= self.merge_threshold:
                self._values[i] = value  # update existing slot
                return
        self._protos.append(k)
        self._values.append(value)

    def recall(self, key: int, context_value: int | None = None) -> int:
        if not self._protos:
            return 0
        q = self.core.encode(key)
        sims = np.array([float(_matmul(p, q)) for p in self._protos])
        attn = np.exp((sims - sims.max()) / self.temp)
        attn /= attn.sum()
        votes = np.zeros(self.n_values)
        for w, v in zip(attn, self._values):
            votes[v] += w
        return int(np.argmax(votes))

    @property
    def param_count(self) -> int:
        # dim per prototype + 1 per stored value id -> GROWS with #slots
        return len(self._protos) * (self.core.dim + 1)

    @property
    def n_slots(self) -> int:
        return len(self._protos)
