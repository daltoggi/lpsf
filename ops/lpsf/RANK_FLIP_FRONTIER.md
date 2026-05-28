# LPSF Rank-Flip Frontier

_Generated 2026-05-26T11:37:46Z_

## Question

Given a retrieval gap **Δr** favoring `path:ev:A` (higher RAG score)
and an attractor differential **Δa** favoring `path:ev:B` (deepened),
at what (Δr, Δa) does LLMPlusLPSF flip from A to B?

## Theoretical prediction

From `c* = argmax(rag_score + attractor_depth)`:

    path:ev:B wins  ⟺  (BASE - Δr/2 + Δa) > (BASE + Δr/2)
                    ⟺  Δa > Δr

Boundary is the linear diagonal **Δa = Δr**. Any deviation indicates
non-additive interaction in the selection layer.

## Empirical grid

Cell shows which candidate LLMPlusLPSF selected at (Δr, Δa).
`A` = `path:ev:A` (RAG winner). `B` = `path:ev:B` (attractor target).
`tie` = both amplitudes equal (boundary cell).

| Δa \ Δr | 0.00 | 0.02 | 0.05 | 0.10 | 0.20 | 0.40 | 0.80 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | tie | A | A | A | A | A | A |
| 0.02 | B | tie | A | A | A | A | A |
| 0.05 | B | B | tie | A | A | A | A |
| 0.10 | B | B | B | tie | A | A | A |
| 0.20 | B | B | B | B | tie | A | A |
| 0.40 | B | B | B | B | B | tie | A |
| 0.80 | B | B | B | B | B | B | tie |
| 1.00 | B | B | B | B | B | B | B |

## Amplitude detail

Each cell: `(amp_A, amp_B)`. Selected = argmax.

| Δa \ Δr | 0.00 | 0.02 | 0.05 | 0.10 | 0.20 | 0.40 | 0.80 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.50/0.50 | 0.51/0.49 | 0.53/0.47 | 0.55/0.45 | 0.60/0.40 | 0.70/0.30 | 0.90/0.10 |
| 0.02 | 0.50/0.52 | 0.51/0.51 | 0.53/0.49 | 0.55/0.47 | 0.60/0.42 | 0.70/0.32 | 0.90/0.12 |
| 0.05 | 0.50/0.55 | 0.51/0.54 | 0.53/0.53 | 0.55/0.50 | 0.60/0.45 | 0.70/0.35 | 0.90/0.15 |
| 0.10 | 0.50/0.60 | 0.51/0.59 | 0.53/0.57 | 0.55/0.55 | 0.60/0.50 | 0.70/0.40 | 0.90/0.20 |
| 0.20 | 0.50/0.70 | 0.51/0.69 | 0.53/0.68 | 0.55/0.65 | 0.60/0.60 | 0.70/0.50 | 0.90/0.30 |
| 0.40 | 0.50/0.90 | 0.51/0.89 | 0.53/0.88 | 0.55/0.85 | 0.60/0.80 | 0.70/0.70 | 0.90/0.50 |
| 0.80 | 0.50/1.30 | 0.51/1.29 | 0.53/1.27 | 0.55/1.25 | 0.60/1.20 | 0.70/1.10 | 0.90/0.90 |
| 1.00 | 0.50/1.50 | 0.51/1.49 | 0.53/1.48 | 0.55/1.45 | 0.60/1.40 | 0.70/1.30 | 0.90/1.10 |

## Boundary verification

✓ **All cells consistent with the linear prediction Δa = Δr.**

The empirical decision boundary matches the equation derived from
`baselines.py::LLMPlusLPSF.respond` exactly. There is no hidden
interaction term in the selection layer — the system does what its
source says it does.

## Interpretation

- Cells where Δa > Δr show `B` (attractor overrode RAG).
- Cells where Δa < Δr show `A` (RAG won).
- The diagonal Δa = Δr is a tie; argmax behavior is implementation-defined
  (Python dict ordering). This is honest information, not a defect.

## Why this experiment matters

Earlier experiments (temperature sensitivity, depth sweep) all returned
'1 distinct path' because they probed a region where one candidate already
dominated. They did not actually map the decision surface.

This sweep explicitly varies the contest margin. The result is a clean,
data-backed statement of exactly when LPSF overrides RAG — namely, when
the attractor differential exceeds the retrieval gap.

## Cost

**$0.** MockLLM only; LLM output text is not consulted by the selection layer.
Running paid APIs here would produce identical results at non-zero cost.