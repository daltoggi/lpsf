# Substrate Recall — the falsifiable test for memory-in-parameters

_Generated 2026-05-28T16:45:13Z_  
_numpy mechanism demo (NOT a language model); dim=48, up to 120 facts, $0_

## The test

Learn `key -> value` facts, then recall each value with an **empty input
context**. If recall works, the memory is in PARAMETERS (true memory). If
it only works with the value retrieved into context, it's fixed-dimension
search over inputs.

## Final empty-context recall (all facts learned)

| System | empty-ctx recall | params | params grow with experience? |
|---|---:|---:|:--:|
| Frozen + RAG | 0.000 | 0 | n/a (learns nothing) |
| Fixed Hebbian | 0.550 | 2304 | no — FIXED |
| Expandable | 1.000 | 5880 | yes — GROWS |

_Chance baseline ≈ 0.008 (1 / #values)._

## Context sanity check

- Frozen+RAG **with** the value in context: recall = 1.000 (it copies).
- Frozen+RAG **without** context: recall = 0.000 (≈ chance).

So Frozen+RAG is perfectly capable — it just has no memory in its
parameters. Remove the context and the knowledge is gone. That is the
hosted-API ceiling: you can never write a fact into the weights.

## Forgetting curve (empty-context recall vs #facts learned)

| #facts | Frozen+RAG | Fixed Hebbian | Expandable |
|---:|---:|---:|---:|
| 2 | 0.000 | 1.000 | 1.000 |
| 5 | 0.000 | 1.000 | 1.000 |
| 10 | 0.000 | 1.000 | 1.000 |
| 15 | 0.000 | 1.000 | 1.000 |
| 20 | 0.000 | 1.000 | 1.000 |
| 30 | 0.000 | 1.000 | 1.000 |
| 40 | 0.000 | 0.975 | 1.000 |
| 50 | 0.000 | 0.920 | 1.000 |
| 60 | 0.000 | 0.917 | 1.000 |
| 120 | 0.000 | 0.550 | 1.000 |

## What this shows (and does not)

- **Frozen+RAG never recalls with empty context.** No parameters change,
  so no fact can live in the substrate. This is exactly a frozen LLM behind
  an API: retrieval rearranges the input, the function is untouched.
- **Fixed Hebbian recalls early but FORGETS as facts exceed its fixed
  capacity.** A single d×d matrix has bounded storage; new facts overwrite
  old ones through crosstalk. This is the 'fixed 12288-dimension' limit in
  miniature.
- **Expandable recalls everything because capacity GROWS with experience.**
  Each distinct fact adds a parameter slot, so nothing is overwritten. This
  is the mechanism that escapes a fixed dimension.

**Honest scope:** this is a numpy associative-memory demo, not an LLM. It
demonstrates the *mechanism* and its *necessity* (fixed capacity forgets;
growth does not). It does NOT show this scales to a transformer, nor that a
real model's pretrained knowledge survives such edits. The real-substrate
step is an open-weights model with LoRA / activation-steering / expandable
memory layers — see `docs/lpsf/SUBSTRATE_NOTES.md`.

Reproduce: `python3 scripts/substrate_recall.py`