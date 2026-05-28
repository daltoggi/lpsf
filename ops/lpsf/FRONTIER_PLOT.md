# Rank-Flip Frontier (Unicode plot)

_Generated 2026-05-26T17:59:38Z_  
_Resolution: 11×11 cells; total 121 runs; MockLLM only ($0)_

```
  Rank-Flip Frontier  (· = A wins  █ = B wins  ◆ = tie)

  Δa↑\Δr→ |0.000.100.190.280.380.470.570.660.760.850.95
  --------+--------------------------------------------
  Δa=1.00 |  █  █  █  █  █  █  █  █  █  █  █  
  Δa=0.90 |  █  █  █  █  █  █  █  █  █  █  ·  
  Δa=0.80 |  █  █  █  █  █  █  █  █  █  ·  ·  
  Δa=0.70 |  █  █  █  █  █  █  █  █  ·  ·  ·  
  Δa=0.60 |  █  █  █  █  █  █  █  ·  ·  ·  ·  
  Δa=0.50 |  █  █  █  █  █  █  ·  ·  ·  ·  ·  
  Δa=0.40 |  █  █  █  █  █  ·  ·  ·  ·  ·  ·  
  Δa=0.30 |  █  █  █  █  ·  ·  ·  ·  ·  ·  ·  
  Δa=0.20 |  █  █  █  ·  ·  ·  ·  ·  ·  ·  ·  
  Δa=0.10 |  █  █  ·  ·  ·  ·  ·  ·  ·  ·  ·  
  Δa=0.00 |  ◆  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  

  The diagonal `Δa = Δr` is exactly the flip boundary,
  predicted by the selection equation c* = argmax(r + a).
```

## Boundary check

✓ All 121 cells consistent with the linear prediction Δa = Δr.

## Reading the plot

- Each row is a value of Δa (top = strong attractor, bottom = no attractor).
- Each column is a value of Δr (left = tied retrieval, right = strong RAG winner).
- A heavy block `█` means LPSF flipped the RAG winner (attractor wins).
- A light dot `·` means RAG kept its winner.
- A diamond `◆` is a numerical tie on the boundary.

The boundary follows the diagonal Δa = Δr exactly. This matches the
amplitude equation in `baselines.py::LLMPlusLPSF.respond` line for line.

Companion document: `RANK_FLIP_FRONTIER.md` (tabular form with exact amplitudes).