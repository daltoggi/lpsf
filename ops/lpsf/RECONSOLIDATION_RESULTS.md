# LPSF H7 Reconsolidation Results

_Generated 2026-05-26T20:30:00Z_

## Question

Does the "plasticity" name in "Landscape-Plastic Semantic Field" have substance?
Or is LPSF effectively a one-way bias injector (deepens stack, but nothing
reverses them)?

## Setup

- **Hypothesis:** `H7_reconsolidation` (newly added)
- **Fixture:** tied RAG scores — `ev:A score = ev:B score = 0.50`
  (the attractor is the sole tiebreaker)
- **LLM:** MockLLM (LLM output does not affect path selection)
- **Cost:** $0

## Scenario phases

| Phase | Operator applied before this phase | Predicted `selected_path` |
|---|---|---|
| initial | `deepen_attractor(path:ev:B, strength=0.6)` | `path:ev:B` (bias took) |
| reversed | `weaken_attractor(path:ev:B, strength=0.6)` (cancels deepen) | NOT `path:ev:B` |
| overridden | `deepen_attractor(path:ev:A, strength=0.8)` (competing) | `path:ev:A` |

## Results

| Phase | LLMPlusLPSF selected | Match prediction? |
|---|---|---:|
| initial | `path:ev:B` | ✓ |
| reversed | `path:ev:A` | ✓ |
| overridden | `path:ev:A` | ✓ |

**Pass: 5/5 unit tests, including the "selected_path actually changed" plasticity check.**

## What this proves

1. **`weaken_attractor` does reverse a `deepen_attractor` bias.** Not by a
   priority-blocked supersede alone — the depth delta actually subtracts and
   the selection layer responds.
2. **Competing attractors override existing ones.** The system supports
   coexisting positive attractors that compete via amplitude, not just
   monotonic stacking.
3. **The "plasticity" name is defensible at the operator-policy level.**
   LPSF is not a one-way bias injector. Bias can be installed, neutralized,
   or out-competed.

## Honest caveats

- This still happens entirely inside the `argmax(r + a)` selection layer.
  Reconsolidation here means "the prior field is mutable in both directions",
  not "the LLM is learning anything new". The bias substrate is plastic;
  the LLM is not.
- The tied-score fixture is deliberately easy: tied RAG scores let any
  attractor differential dominate. In real fixtures with skewed RAG scores,
  the depth needed to flip is bounded by the rank-flip frontier
  (see `RANK_FLIP_FRONTIER.md`).
- No experiment yet shows that the system *gracefully* heals an erroneous
  bias — only that it *can* be reversed by explicit operator calls.
  An interesting follow-up: does decay-over-time (via `half_life`) achieve
  the same recovery automatically?

## Relation to other experiments

| Experiment | Showed |
|---|---|
| H6 adversarial | LPSF can override RAG (controllability) |
| Rank-flip frontier | Exactly *when* it overrides (Δa > Δr) |
| **H7 reconsolidation** | **And it can be undone (true bidirectional plasticity)** |
| Temperature sensitivity | Path selection is architecturally decoupled from LLM noise |
| Depth sweep | The H4 fixture was too easy to find a noise threshold |

Together these establish that the substrate is **controllable, predictable,
and reversible** — the three properties a memory layer needs to be more
than a one-way bias injector.
