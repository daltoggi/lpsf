# 07 — Risk Register

## R1 — Project Becomes Ordinary RAG

Risk:

Codex implements vector search and calls it memory.

Mitigation:

Require persistent landscape marks and before/after response shift tests.

## R2 — Over-Metaphorization

Risk:

Terms like gravity, quantum, epigenetic, field remain poetic rather than operational.

Mitigation:

Every term must map to a data structure or scoring function.

## R3 — Private 2nd Brain Leakage

Risk:

Raw notes enter commits, logs, prompts, screenshots, or external services.

Mitigation:

Use sanitized summaries, source hashes, draft-only write-back, and strict approved directories.

## R4 — Unbounded Autonomy

Risk:

Codex runs a vague goal and makes broad changes.

Mitigation:

Use `/plan` first, define stopping condition, force checkpoint logs.

## R5 — False Proof

Risk:

The prototype appears smart because the prompt tells it the answer.

Mitigation:

Compare against baselines and blind-ish test prompts.

## R6 — State Pollution

Risk:

Wrong feedback deepens bad attractors.

Mitigation:

Use outcome score, decay, manual review for strong/long marks.

## R7 — Forgetting Too Much or Too Little

Risk:

Model either loses useful context or becomes noisy.

Mitigation:

Four-way memory policy: raw, summary, landscape, forget.

## R8 — Source Hallucination

Risk:

Research notes invent paper claims.

Mitigation:

Paper notes must include exact source metadata, claim/evidence distinction, and uncertainty.

## R9 — Existing Notes Are Damaged

Risk:

Codex reorganizes or overwrites the user’s 2nd brain.

Mitigation:

Read-only by default; write only to draft folder.

