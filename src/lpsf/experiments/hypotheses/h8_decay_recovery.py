"""H8: decay-driven recovery — half_life produces natural attractor weakening.

Where H7 showed that bias can be reversed by an explicit `weaken_attractor`
call, H8 shows that bias also weakens *automatically* when `apply_decay` is
invoked with `now > last_activation_at + 2*half_life`. This is the
time-based companion to H7's operator-based reversal.

Because `apply_decay` is not part of the standard 8-operator scenario
dispatch (it takes `now`, not the standard plasticity-mark kwargs), H8 uses
a custom orchestration in the corresponding test rather than fitting into
`run_experiment`.

Scenario (tied RAG fixture so the attractor alone decides):
  Phase initial:  deepen path:ev:B with strength=0.6, half_life=100
                  → LPSF selects path:ev:B (bias in effect).
  Phase decayed:  apply_decay with now = last_activation_at + 300
                  → effective depth(B) ≈ 0.6 * 0.5^3 = 0.075
                  → no longer enough to outweigh A; selection flips back to A.
"""

from __future__ import annotations

from typing import Any, Dict, List


HALF_LIFE_SECONDS = 100
INITIAL_DEPTH = 0.2  # initial depth, just enough to flip a small RAG margin
# Score margin Δr = 0.05 in favor of A; depth Δa = 0.20 in favor of B.
# Initially Δa (0.20) > Δr (0.05) so B wins.
# After 3 half-lives: Δa shrinks to 0.025, less than Δr=0.05; A wins.
ELAPSED_HALF_LIVES = 3


def build_rag_fixture() -> Dict[str, List[Dict[str, Any]]]:
    """Near-tied RAG scores; A has a small (0.05) BM25 edge.

    The asymmetry is essential: if both candidates were perfectly tied,
    decay would only ever push the attractor toward zero (never below),
    and B would still win on any positive remaining depth. By giving A
    a small natural advantage, decay produces a real selection flip
    when Δa shrinks below Δr.
    """
    return {
        "tied query": [
            {
                "id": "ev:A",
                "score": 0.525,
                "sanitized_summary": "candidate A (small RAG edge)",
                "source_type": "synthetic",
            },
            {
                "id": "ev:B",
                "score": 0.475,
                "sanitized_summary": "candidate B (initial bias target)",
                "source_type": "synthetic",
            },
        ],
    }
