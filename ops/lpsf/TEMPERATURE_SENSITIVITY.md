# LPSF Temperature Sensitivity Report

_Generated 2026-05-26T10:59:53Z (sonnet run); haiku run 2026-05-26T10:52:35Z_

## Setup

| | haiku run | sonnet run |
|---|---|---|
| **Model** | claude-haiku-4-5 | claude-sonnet-4-5 |
| **Hypothesis** | H4_snapshot_reproducibility | H4_snapshot_reproducibility |
| **Seeds** | 10 per temperature | 10 per temperature |
| **Cost** | $0.04 | $0.09 |
| **Wall time** | 173.3s | 260.9s |

## Results

Both models: all temperatures → 1 distinct path, 30/30 pass.

| Temperature | haiku distinct paths | sonnet distinct paths |
|---:|---:|---:|
| 0.0 | 1 (`path:ev:M1`) | 1 (`path:ev:M1`) |
| 0.7 | 1 (`path:ev:M1`) | 1 (`path:ev:M1`) |
| 1.0 | 1 (`path:ev:M1`) | 1 (`path:ev:M1`) |

## Architectural interpretation (why this is trivially true — and why that matters)

In `LLMPlusLPSF`, path selection is:

```python
selected = max(amplitudes, key=amplitudes.get)
# where amplitudes[cand] = rag_score[cand] + attractor_depth[cand]
```

**The LLM response text is not used to rank candidates.** Temperature changes the
logged `raw_llm_response` but has zero effect on `selected_path`.

So "1 distinct path at all temperatures" is correct but for a non-mysterious reason:
the path selection is **deterministic by architecture** once evidence scores and
attractor state are fixed. It is not that LPSF *overcomes* LLM sampling noise —
it is that LPSF *bypasses* it entirely at the path-selection layer.

### What this finding actually proves

- **Stability claim (valid)**: LPSF path selection is invariant to LLM temperature.
  Any downstream consumer of `selected_path` gets the same answer regardless of
  how stochastic the underlying LLM is.
- **"Attractor dominates noise" framing (misleading)**: Accurate result, wrong causal
  story. The independence from noise is architectural, not emergent.
- **Implication for future work**: To test whether LPSF *guidance* survives LLM
  variability in a non-trivial way, the response text itself must be used for
  candidate selection (e.g. LLM-as-reranker), then tested at high temperature.

_See `ops/lpsf/ADVERSARIAL_RESULTS.md` for the H6 test, which IS a non-trivial
independence check._
