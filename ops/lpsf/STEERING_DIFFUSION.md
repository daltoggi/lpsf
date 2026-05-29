# Mean-Centered Steering — testing the Grover-diffusion hunch

_Generated 2026-05-29T14:58:11Z_  
_Qwen2.5-0.5B (frozen), layer 12. CAA-style vectors ([2312.06681](https://arxiv.org/abs/2312.06681)); centering = reflect-about-mean._

## The hunch

Grover amplitude amplification amplifies a target by amplifying its **deviation from the mean** (sign-flip + reflect-about-mean), and over-iterating degrades it. Phase S showed our concept vectors share a common component (cos +0.73) that, when summed, amplifies and washes out. The transferable idea: subtract the shared mean, steer along the deviation `v_i − v̄`. Predicted to land near the cos ≈ 0 sweet spot additive composition needs.

## Result 1 — does centering hit cos ≈ 0?

| method | derivation | concept-concept cosines | max\|cos\| |
|---|---|---|---:|
| raw | concept − office (Phase S Pt1) | ocean·music=+0.73, ocean·cooking=+0.75, music·cooking=+0.75 | 0.75 |
| ortho | concept − other concepts (Phase S Pt3) | ocean·music=-0.58, ocean·cooking=-0.58, music·cooking=-0.33 | 0.58 |
| centered | raw − shared-mean (the hunch) | ocean·music=-0.58, ocean·cooking=-0.57, music·cooking=-0.33 | 0.58 |

**Partial:** centering gives the smallest |cos| (0.58) — vs raw (+0.75, shared component) and ortho (0.58, anti-correlated). Centering helped but did not clearly win; see caveats.

## Result 2 — does it widen the coexistence window?

ocean+music word counts (ocean/music) per per-concept alpha. A 'coexistence point' = both > 0.

| method | α=2 | α=4 | α=6 | α=8 | α=10 | coexist pts |
|---|---|---|---|---|---|---:|
| raw | 0/0 | 0/1 | 2/0 | 9/0 | 5/5 | 1 |
| ortho | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 0 |
| centered | 0/0 | 0/0 | 0/0 | 0/0 | 1/0 | 0 |

**Coexistence points: raw=1, ortho=0, centered=0** (out of 5 alphas).

**Hunch did not pan out empirically.** Centering improved on raw's cosine but matched ortho (NOT cos≈0), and did NOT widen coexistence — it reproduced the ortho failure. There is a rigorous reason (below).

## Why centering overshoots — and where the Grover analogy breaks

Mean-centering imposes Σᵢ(vᵢ − v̄) = 0. For k unit vectors that sum to zero, the pairwise dot products satisfy Σ_{i≠j} vᵢ·vⱼ = −Σ|vᵢ|², so the **average pairwise cosine is forced to −1/(k−1)**. For k=3 that is **-0.50** — and the measured centered average is **-0.50**. The match confirms it: with only 3 concepts you **cannot center your way to cos≈0** — the sum-to-zero constraint pushes you past orthogonal into anti-correlation. (This is also why `ortho` and `centered` coincide: contrasting a concept against the mean of the others is the same move up to scale.)

**This is exactly where the quantum analogy breaks — on N.** Grover's diffusion (reflect about the mean) is *benign* because N is enormous: the Σ=0 constraint is spread over N states, so each non-target picks up only ~−1/N ≈ 0 correlation. Grover needs large N not just for the √N speedup but for its diffusion to be non-destructive. Our problem has k=3, so the identical operation forces −0.5 and destroys coexistence. The hunch was structurally right (amplify deviation from the mean) and fails for a precise, satisfying reason that traces back to the quantum setting's large-N assumption.

**The actual fix it points to:** to reach cos≈0 with few concepts you need explicit orthogonalization (Gram-Schmidt) that targets 0 directly, or many more concepts so the −1/(k−1) floor approaches 0. Centering/contrast can't do it.

## Honest scope

It is an ANALOGY, not quantum: no superposition, no √N speedup, no unitarity — we borrow only the reflect-about-mean operator structure, which is itself the known CFG / contrastive-decoding / mean-ablation family. The value is that the *need* (cos ≈ 0) was derived from our own Phase S failures, and the *fix* came from the user's quantum intuition. 3 concepts, 1 layer, 0.5B, keyword metric.

Builds on `STEERING_GEOMETRY.md` and `MULTICONCEPT_STEERING.md`.
Reproduce: `python3 scripts/steering_diffusion.py`