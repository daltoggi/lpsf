"""LoRAMemory — LPSF operators mapped onto LoRA weight space.

This is the bridge between the two tracks:

  Reranking track (v0.1): LPSF operators act on `attractor_depth` scores
    that bump reranking amplitudes. The LLM itself never changes.

  Substrate track (this module): the same operators act on LoRA adapter
    WEIGHTS, so the LLM's parametric memory changes. `deepen` is a gradient
    step toward a fact; `weaken` is a gradient step away; `decay` is
    exponential weight shrinkage.

The LPSF operator vocabulary (deepen/weaken/decay/reconsolidate) is
preserved. Only the substrate changes — from rerank score to LoRA weight.

Status: DESIGN STUB. The mathematical structure and contracts are specified
below. The numpy proof-of-concept is fully functional. The full MLX/LoRA
implementation depends on the multi-fact interference results — specifically,
whether sequential learning already generalizes or whether a proper weight-
space EWC penalty is needed.

See ops/lpsf/MULTIFACT.md for the interference measurements that motivate
the design choices here.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Design contracts (not yet wired to MLX)
# ---------------------------------------------------------------------------

class LoRAMemorySpec:
    """Specification of the LoRA-substrate LPSF operator semantics.

    This is a documentation class, not a runtime one. It records the
    mapping from LPSF operators → LoRA weight operations.

    Operator → weight action:
    ──────────────────────────────────────────────────────────────────
    deepen_attractor(fact, strength, half_life)
        Forward pass on `fact`'s Q&A pairs, scale gradient by `strength`,
        take one gradient step on the LoRA matrices. Records the
        `source_marks` (which parameter tensors were updated and by how much)
        so the effect can be reversed by `weaken_attractor`.

    weaken_attractor(fact, strength)
        Apply an L2 penalty toward the pre-deepen weight checkpoint for
        `fact`'s parameter region. Equivalent to EWC-lite on the targeted
        parameters. If no checkpoint exists, shrink the weight delta by
        `strength` fraction.

    decay(half_life, now)
        Exponential decay of all LoRA deltas: Δ ← Δ * 0.5^(elapsed/half_life).
        Applied globally or per-mark. Implements the same time-based
        recovery as the numpy H8 experiment, now on real weights.

    reconsolidate_memory(fact_a, fact_b)
        Merge the LoRA deltas for two facts that share evidence; prunes
        redundant gradient directions. Analogous to the DB-layer operator.

    open_path / inhibit_path
        Increase / decrease the logit contribution of a specific token
        sequence by updating the LoRA output projection for that path.
        Requires token-level targeting (not yet implemented).
    ──────────────────────────────────────────────────────────────────

    Storage contract:
        Each `deepen_attractor` call writes a `plasticity_mark` row to the
        LPSF SQLite state DB (same schema as v0.1) with:
            operator_type = "deepen_attractor"
            target_id     = fact identifier (e.g. "zarnak_2087")
            strength      = the gradient scale used
            decay_state   = JSON with lora_delta_norm, param_keys

        The state DB is the single source of truth for what has been learned
        and how strongly. `weaken` and `decay` look up their targets via
        standard `_load_attractors` queries.
    """


# ---------------------------------------------------------------------------
# Numpy proof-of-concept (runnable today)
# ---------------------------------------------------------------------------

class LoRAWeightMemory:
    """Numpy stand-in for the LoRA weight memory. Runnable without MLX.

    Models LoRA as two matrices A (r×d_in) and B (d_out×r).
    The effective weight delta is ΔW = B @ A (d_out×d_in).

    `deepen`: one gradient step toward a (key, value) association.
    `weaken`: step away (EWC-lite: penalise deviation from pre-deepen state).
    `decay`:  exponential shrink of B, A toward zero.

    Empty-context recall: cosine similarity of ΔW @ key_enc to value_enc.
    """

    def __init__(self, *, d_in: int = 64, d_out: int = 64, rank: int = 4,
                 lr: float = 0.1, seed: int = 0) -> None:
        import numpy as np
        rng = np.random.default_rng(seed)
        # LoRA matrices, initialised near zero (standard practice).
        self._A = rng.standard_normal((rank, d_in)) * 0.01
        self._B = np.zeros((d_out, rank))
        self._d_in = d_in
        self._d_out = d_out
        self._rank = rank
        self._lr = lr
        self._marks: List[Dict[str, Any]] = []  # plasticity_marks

    # ---- core linear algebra helpers ------------------------------------

    def _delta_w(self) -> "np.ndarray":
        import numpy as np
        from .core import _matmul
        return _matmul(self._B, self._A)

    def encode(self, key: "np.ndarray") -> "np.ndarray":
        """Apply ΔW to a key encoding and return the recalled value direction."""
        from .core import _matmul
        return _matmul(self._delta_w(), key)

    def recall(self, key: "np.ndarray", value_embs: "np.ndarray") -> int:
        """Return the index of the nearest value embedding to ΔW @ key."""
        import numpy as np
        from .core import _matmul
        out = _matmul(self._delta_w(), key)
        sims = _matmul(value_embs, out)
        return int(np.argmax(sims))

    # ---- LPSF operators --------------------------------------------------

    def deepen(self, key: "np.ndarray", value: "np.ndarray",
               strength: float = 1.0) -> Dict[str, Any]:
        """One gradient step toward associating key → value.

        Gradient of MSE loss (ΔW @ key - value)^2 w.r.t. A and B.
        """
        import numpy as np
        from .core import _matmul
        err = _matmul(self._delta_w(), key) - value          # (d_out,)
        dB = np.outer(err, _matmul(self._A, key))            # (d_out, rank)
        dA = _matmul(self._B.T, err[:, None]) * key[None, :] # (rank, d_in)
        self._B -= self._lr * strength * dB
        self._A -= self._lr * strength * dA
        delta_norm = float(np.linalg.norm(dB) + np.linalg.norm(dA))
        mark = {"op": "deepen", "strength": strength, "delta_norm": delta_norm}
        self._marks.append(mark)
        return mark

    def weaken(self, key: "np.ndarray", strength: float = 0.5) -> Dict[str, Any]:
        """Shrink the weight component aligned with key (targeted EWC-lite)."""
        import numpy as np
        from .core import _matmul
        # Project out the key direction from A: remove key's contribution.
        k_unit = key / (np.linalg.norm(key) + 1e-8)
        proj = _matmul(self._A, k_unit[:, None]) * k_unit[None, :]  # (rank, d_in)
        self._A -= strength * proj
        delta_norm = float(np.linalg.norm(proj))
        mark = {"op": "weaken", "strength": strength, "delta_norm": delta_norm}
        self._marks.append(mark)
        return mark

    def decay(self, half_life: float, elapsed: float) -> float:
        """Exponential decay of all LoRA weights: scale by 0.5^(elapsed/half_life)."""
        factor = math.pow(0.5, elapsed / max(half_life, 1e-8))
        self._A *= factor
        self._B *= factor
        return factor

    @property
    def param_count(self) -> int:
        return self._A.size + self._B.size  # FIXED (rank × (d_in + d_out))

    @property
    def n_marks(self) -> int:
        return len(self._marks)
