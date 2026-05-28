# LPSF Attractor Depth Sweep

_Generated 2026-05-26T10:59:15Z_

## Setup

- **Model:** claude-haiku-4-5
- **Temperature:** 1.0 (maximum noise)
- **Seeds:** 10 per depth
- **Baselines:** LLMPlusRAG, LLMPlusLPSF
- **Wall time:** 0.1s (all cache hits from prior temp-sensitivity run)

## Results

| Attractor depth | Distinct LLMPlusLPSF paths | Pass rate | Path observed |
|---:|---:|---:|---|
| 0.05 | 1 | 10/10 | `path:ev:M1` |
| 0.10 | 1 | 10/10 | `path:ev:M1` |
| 0.20 | 1 | 10/10 | `path:ev:M1` |
| 0.40 | 1 | 10/10 | `path:ev:M1` |
| 0.60 | 1 | 10/10 | `path:ev:M1` |
| 0.80 | 1 | 10/10 | `path:ev:M1` |

## Why no threshold was found — and what this reveals

In the H4 fixture `ev:M1` has RAG score 0.55 and `ev:M2` has 0.45.
Even at **depth=0** (no attractor) `path:ev:M1` wins on RAG score alone.
For any `depth > 0` the margin widens.

Because `selected = max(rag_score + attractor_depth)` and the LLM response
text is not used for path ranking (see temperature sensitivity report),
no noise-tolerance threshold can exist in this fixture regardless of depth
or temperature.

**Conclusion**: this sweep confirmed the architecture works correctly (attractor
amplitudes are applied) but the H4 fixture is too easy to find a meaningful
threshold. A proper depth-threshold experiment requires competing candidates
with equal RAG scores where the attractor is the sole tiebreaker.

## Proposed follow-up

Design a "tied-score" fixture: `ev:A score=0.50, ev:B score=0.50`, deepen
`path:ev:A` at varying depths, then determine the minimum depth needed to
guarantee `path:ev:A` wins deterministically. At equal RAG scores the margin
is exactly the attractor depth, which would give a clean threshold report.

_Run with `scripts/depth_sweep.py --help` to update._
