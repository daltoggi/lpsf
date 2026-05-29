# Multi-Fact LoRA Interference — Sequential Learning

_Generated 2026-05-29T06:19:30Z_  
_Model: mlx-community/Qwen2.5-0.5B-Instruct-4bit. 5 fictional facts taught one at a time._  
_Mixed training per fact: 6 fact paraphrases + 12 anchor Q&A × 2._

## The question

After the single-fact memory test (recall 1.00) and forgetting analysis
(79% retention), the natural next question: does interference accumulate
as more facts are added? Can the model hold 2, 3, 5 independent facts?

## Sequential learning — avg recall of all taught facts vs #facts

| Step | New fact taught | Recall of taught facts | Key question |
|---:|---|---:|---|
| 1 | Zarnak Protocol | 1.00 | added successfully |
| 2 | Korethian Codex | 0.50 | degraded previous |
| 3 | Velastrom Decree | 0.33 | degraded previous |
| 4 | Syndaran Accord | 0.25 | degraded previous |
| 5 | Quelthar Manifesto | 0.20 | degraded previous |

## Per-fact recall at each step

| Step | F1 | F2 | F3 | F4 | F5 |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.00 | — | — | — | — |
| 2 | 0.00 | 1.00 | — | — | — |
| 3 | 0.00 | 0.00 | 1.00 | — | — |
| 4 | 0.00 | 0.00 | 0.00 | 1.00 | — |
| 5 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |

## Findings

- After teaching all 5 facts sequentially, average recall = **0.20**.
- Recall of the FIRST fact (Zarnak Protocol) after 4 more were added = **0.00**.

**Last-write-wins:** the pattern is perfectly destructive. After each new fact, *every* previous fact drops instantly to 0.00 — not gradual degradation but complete replacement. The single LoRA adapter acts as a **single-slot memory**: it holds exactly one fictional fact at a time, always the most recently written.

This is distinct from the forgetting we saw in the general-knowledge experiment (79% retention). General knowledge survives because it is anchored by the base model's strong priors and the anchor training. Fictional facts — which have *no* competing gradient from pretraining — are entirely at the mercy of the most recent gradient update.

**The severity is structural:** a single shared adapter has no mechanism to separate the storage of different facts. Every gradient step simultaneously reads from and writes to the same parameter space. EWC or replay is not just "nice to have" for this setting — it is the minimum requirement for a system that can hold more than one fact.

## Connection to the substrate track (coming next)

These results directly motivate the LPSF operator → LoRA mapping:
- `deepen_attractor(fact, strength)` → increase LoRA weight magnitude for that fact
- `weaken_attractor(fact)` → regularize weights down (EWC penalty)
- `decay(half_life)` → exponential weight decay over time

The interference curve shows the cost we're paying *without* such a mechanism.
With it, decay + selective protection would replace the blunt mixed-training anchor.

**Honest scope:** 5 facts, 0.5B model, single LoRA head. Larger models, rank-constrained adapters, and dedicated memory layers are expected to behave differently. This quantifies the baseline.