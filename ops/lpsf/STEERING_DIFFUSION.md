# Mean-Centered Steering — testing the Grover-diffusion hunch

_Generated 2026-05-29T15:11:56Z_  
_Qwen2.5-0.5B (frozen), layer 12. CAA-style vectors ([2312.06681](https://arxiv.org/abs/2312.06681)); centering = reflect-about-mean._

## The hunch

Grover amplitude amplification amplifies a target by amplifying its **deviation from the mean** (sign-flip + reflect-about-mean), and over-iterating degrades it. Phase S showed our concept vectors share a common component (cos +0.73) that, when summed, amplifies and washes out. The transferable idea: subtract the shared mean, steer along the deviation `v_i − v̄`. Predicted to land near the cos ≈ 0 sweet spot additive composition needs.

## Result 1 — does centering hit cos ≈ 0?

| method | derivation | concept-concept cosines | max\|cos\| |
|---|---|---|---:|
| raw | concept − office (Phase S Pt1) | ocean·music=+0.73, ocean·cooking=+0.75, music·cooking=+0.75 | 0.75 |
| ortho | concept − other concepts (Phase S Pt3) | ocean·music=-0.58, ocean·cooking=-0.58, music·cooking=-0.33 | 0.58 |
| centered | raw − shared-mean (the hunch) | ocean·music=-0.58, ocean·cooking=-0.57, music·cooking=-0.33 | 0.58 |
| gs | Gram-Schmidt orthogonalized (targets cos=0) | ocean·music=-0.00, ocean·cooking=-0.00, music·cooking=+0.00 | 0.00 |

**Centering does NOT hit cos≈0** (it matches ortho at 0.58; the math is in 'Why centering overshoots' below). **Gram-Schmidt does** — max|cos| = 0.00 by construction. It is the only method that targets orthogonality directly instead of overshooting to −1/(k−1).

## Result 2 — does it widen the coexistence window?

ocean+music word counts (ocean/music) per per-concept alpha. A 'coexistence point' = both > 0.
## Result 2 — does it widen the coexistence window?

ocean+music word counts (ocean/music) per per-concept alpha. A 'coexistence point' = both > 0.

| method | α=2 | α=4 | α=6 | α=8 | α=10 | coexist pts |
|---|---|---|---|---|---|---:|
| raw | 0/0 | 0/1 | 2/0 | 9/0 | 5/5 | 1 |
| ortho | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 0 |
| centered | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 0 |
| gs | 0/0 | 0/3 | 0/5 | 0/7 | 0/5 | 0 |

**Coexistence points: raw=1, ortho=0, centered=0, gs=0** (out of 5 alphas).

**Centering reproduced the ortho failure** — it matched ortho's cosine (NOT cos≈0) and did not widen the window. There is a rigorous reason (next section).

**Gram-Schmidt hit cos≈0 — and STILL failed to balance (0 coexistence points).** music dominated (total 20 words) while ocean vanished (0). The cause is precise: GS is **order-dependent**. The first concept in the order keeps the full shared 'vivid' component, so its unit vector is concept-*weak* (diluted by the shared junk); later concepts get that component projected out, so per unit norm they are concept-*pure* and dominate at equal alpha. **So cos≈0 is necessary but NOT sufficient for balanced composition — the vectors must also be balanced in concept-purity.** Symmetric purity needs symmetric shared-removal (centering), but centering overshoots to −1/(k−1) at small k. Having BOTH cos≈0 AND symmetry requires large k — the large-N theme, one more time. The geometry was necessary, not sufficient; and we know exactly why.

## Why centering overshoots — and where the Grover analogy breaks

Mean-centering imposes Σᵢ(vᵢ − v̄) = 0. For k unit vectors that sum to zero, the pairwise dot products satisfy Σ_{i≠j} vᵢ·vⱼ = −Σ|vᵢ|², so the **average pairwise cosine is forced to −1/(k−1)**. For k=3 that is **-0.50** — and the measured centered average is **-0.50**. The match confirms it: with only 3 concepts you **cannot center your way to cos≈0** — the sum-to-zero constraint pushes you past orthogonal into anti-correlation. (This is also why `ortho` and `centered` coincide: contrasting a concept against the mean of the others is the same move up to scale.)

**This is exactly where the quantum analogy breaks — on N.** Grover's diffusion (reflect about the mean) is *benign* because N is enormous: the Σ=0 constraint is spread over N states, so each non-target picks up only ~−1/N ≈ 0 correlation. Grover needs large N not just for the √N speedup but for its diffusion to be non-destructive. Our problem has k=3, so the identical operation forces −0.5 and destroys coexistence. The hunch was structurally right (amplify deviation from the mean) and fails for a precise, satisfying reason that traces back to the quantum setting's large-N assumption.

**The actual fix it points to:** to reach cos≈0 with few concepts you need explicit orthogonalization (Gram-Schmidt) that targets 0 directly, or many more concepts so the −1/(k−1) floor approaches 0. Centering/contrast can't do it.

## Honest scope

It is an ANALOGY, not quantum: no superposition, no √N speedup, no unitarity — we borrow only the reflect-about-mean operator structure, which is itself the known CFG / contrastive-decoding / mean-ablation family. The value is that the *need* (cos ≈ 0) was derived from our own Phase S failures, and the *fix* came from the user's quantum intuition. 3 concepts, 1 layer, 0.5B, keyword metric.

Builds on `STEERING_GEOMETRY.md` and `MULTICONCEPT_STEERING.md`.
Reproduce: `python3 scripts/steering_diffusion.py`