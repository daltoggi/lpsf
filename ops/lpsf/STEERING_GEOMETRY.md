# Steering Geometry & Layer Locus — the mechanism behind Phase Q

_Generated 2026-05-29T14:19:11Z_  
_Qwen2.5-0.5B (frozen). Contrastive mean-difference vectors (CAA, [2312.06681](https://arxiv.org/abs/2312.06681))._

## Part 1 — Are concept vectors orthogonal? (layer 12)

Steering vectors derived as `mean_act(concept prompts) - mean_act(office prompts)`.

| pair | cosine |
|---|---:|
| ocean · music | +0.732 |
| ocean · cooking | +0.747 |
| music · cooking | +0.750 |
| ocean · random | +0.011 |
| music · random | +0.001 |
| cooking · random | -0.045 |

- Raw concept-signal norms (pre-normalization): {'ocean': 1.4, 'music': 0.9, 'cooking': 1.3}
- Mean residual norm at layer 12: ~45

**Surprise (this refuted my prior).** Concept pairs are NOT orthogonal — they share a strong common direction (cos up to +0.75), while each is near-orthogonal to a random vector (~0). The cause is the contrast set: `concept - office` captures both the concept AND a shared 'vivid/sensory vs bureaucratic' component that every concept has relative to office text. That shared component leaks into all three vectors. This is the classic CAA caveat — a steering vector is only as clean as its contrast set.

This **re-explains the Phase Q washout**: adding ocean+music does NOT cancel by direction; instead the shared component **adds constructively (~2x)** and dominates. At high alpha that doubled common push overshoots off-manifold → neither concept surfaces (washout). At moderate alpha it stays on-manifold → both surface (the coexistence window). So washout is driven by an amplified shared confound, not by clean per-concept magnitude.

## Part 3 — The 'fix' that backfired (and taught the real lesson)

Diagnosis: the +0.73 cosine is a shared component the office contrast leaks in. Proposed fix: derive `mean_act(concept) - mean_act(OTHER concepts)` so the shared part cancels. Predicted cosines drop toward 0.

| pair | cosine (office contrast) | cosine (ortho contrast) |
|---|---:|---:|
| ocean · music | +0.732 | -0.576 |
| ocean · cooking | +0.747 | -0.576 |
| music · cooking | +0.750 | -0.334 |

**Diagnosis confirmed, but the fix overshot.** The shared component was real — removing it drove cosines from +0.75 all the way to -0.58 (anti-correlated), not to ~0. Contrasting ocean against {music, cooking} builds a vector that points toward ocean AND *away from* music/cooking by construction — so the concept vectors now actively oppose each other.

Coexistence re-test (ocean+music, orthogonalized vectors):

| per-concept alpha | ocean | music |
|---:|---:|---:|
| 4 | 0 | 0 |
| 10 | 1 | 0 |

**Coexistence got WORSE, not better** (vs the office-contrast window of ocean≈3/music≈4 at alpha 4 in `MULTICONCEPT_STEERING.md`). Anti-correlated vectors cancel each other's concept-specific parts when summed.

## Part 2 — Where is the concept steerable? (layer sweep)

Ocean vector (office contrast), alpha=8, ocean-word count over 3 neutral prompts:

| layer | ocean words | residual norm |
|---:|---:|---:|
| 4 | 11 | 45.2 |
| 8 | 13  ← strongest | 45.2 |
| 12 | 6 | 45.3 |
| 16 | 1 | 46.6 |
| 20 | 0 | 58.0 |

**Reading:** steering strength is strongly layer-dependent — peaks at the early-mid layers here (layer 8) and collapses toward late layers, where the residual norm also grows (so a fixed alpha is a smaller push-fraction — a norm-budget confound). Concept directions are most linearly steerable at a mid-network locus, consistent with CAA.

## What this deepened (triangulated by two failures)

Two contrast strategies, two instructive failures that bracket the real requirement:

- **office contrast → cos +0.73** (shared confound): summing amplifies the common component → washout at high alpha, coexistence only in a narrow window and for the *wrong* reason (the shared part carries it, not the concepts).
- **ortho contrast → cos −0.58** (anti-correlated): summing cancels the concept-specific parts → coexistence is worse.

**The real lesson:** additive multi-concept steering needs concept directions that are genuinely **orthogonal (cos ≈ 0)** — neither sharing a dominant common component nor opposing each other. Crude contrastive mean-difference does not reliably produce that; the cosine is an artifact of the contrast set (+0.73 one way, −0.58 the other), and ≈0 was not hit by either. This is the honest geometric limitation of naive activation steering for composition — and it is exactly why the literature uses more careful vector construction (orthogonalization toward 0, conditional/per-concept methods) rather than raw sums. Rediscovered here by hand: hypothesis → measure → refute → 'fix' → refute again → real requirement.

## Honest scope

3 concepts, one 0.5B model, keyword metric, ||mean activation|| as a rough residual-scale proxy (per-token norms are larger). Conclusions are directional, not precise capacity measurements. Builds on `MULTICONCEPT_STEERING.md`.

Reproduce: `python3 scripts/steering_geometry.py`