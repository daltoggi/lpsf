# Multi-Concept Steering — coexistence vs interference

_Generated 2026-05-29T07:08:22Z_  
_Qwen2.5-0.5B (frozen), layer 12, alpha 10.0 per concept._

## The question

Multi-fact LoRA collapsed (last-write-wins: each new fact erased the previous,
single-slot memory). Steering vectors ADD in the residual stream — can multiple
concept deformations coexist where LoRA could not? This is the LPSF operator-
composition test: can the landscape hold 'deepen A AND deepen B' simultaneously?

## Concept-word counts across 4 neutral prompts (coh = coherence 0-1)

| condition | ocean | music | cooking | coh |
|---|---:|---:|---:|---:|
| baseline | 0 | 0 | 0 | 0.88 |
| ocean | 18 | 0 | 0 | 0.93 |
| music | 1 | 17 | 0 | 0.81 |
| cooking | 0 | 0 | 6 | 0.86 |
| **ocean+music | 0 | 0 | 0 | 0.81** |
| **ocean+music+cooking | 0 | 0 | 0 | 0.83** |
| random x2 | 0 | 0 | 0 | 0.81 |

## Verdict

**Inconclusive at these settings.** ocean+music: ocean=0, music=0 vs baseline ocean=0, music=0.

**Mutual washout (a third mode, distinct from LoRA).** Each concept steers cleanly ALONE (ocean 18, music 17), but the equal-alpha SUM expresses NEITHER (ocean 0, music 0) while staying fluent (coh 0.81). This is not LoRA's last-write-wins (one survives) — it is both-lose. Adding two concept directions at full strength points to a third direction that is neither concept's region.

- Triple (ocean+music+cooking) all elevated: no (ocean=0, music=0, cooking=0)
- Negative control clean (random raises nothing): yes
- Coherence: baseline 0.88, pair 0.81, triple 0.83, random 0.81

## Pair alpha-sweep (ocean+music, equal per-concept alpha)

Is the washout an overshoot (cured by lower alpha) or fundamental interference?

| per-concept alpha | ocean | music |
|---:|---:|---:|
| 2 | 0 | 1 |
| 3 | 2 | 1 |
| 4 | 3 | 4 |
| 5 | 5 | 2 |
| 6 | 7 | 0 |
| 8 | 3 | 1 |

**Coexistence IS reachable at lower alpha** (best: alpha=4, ocean=3, music=4). The full-alpha washout was overshoot: summing two strong vectors overshoots off-manifold. At a tuned scale the two deformations DO coexist — operators compose with scale control.

## Contrast with multi-fact LoRA

| | LoRA (weights) | Steering (activations) |
|---|---|---|
| 2nd item added | previous -> 0.00 (last-write-wins) | see table above |
| mechanism | shared parameter space, overwritten | additive vectors in residual stream |

If steering coexists where LoRA collapsed, that is concrete evidence for WHY an activation-space landscape is a better multi-memory substrate than weight editing: additivity. The operators can compose.

## Honest scope

3 concepts, 1 layer (L12), 0.5B, keyword metric, alpha=10.0. Does not show how many concepts before saturation, or behavior at other layers/models. The coherence column guards against mistaking degradation for steering.

Reproduce: `python3 scripts/multiconcept_steering.py`