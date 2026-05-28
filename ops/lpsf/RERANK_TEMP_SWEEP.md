# LPSF LLM-as-Reranker Temperature Sweep

_Generated 2026-05-26T11:52:10Z_

## Question

With `LLMPlusLPSFRerank` (β>0), LLM output text **does** affect path
selection via pairwise voting. Does temperature now produce variance,
and does the LPSF attractor (γ>0) reduce that variance?

## Setup

- **Model:** claude-haiku-4-5
- **Baseline:** LLMPlusLPSFRerank with α=1.0, β=1.0, γ ∈ {0.0, 0.5}
- **Fixture:** tied RAG scores (ev:A = ev:B = 0.50)
- **Attractor:** when γ>0, deepen path:B with strength 0.5
- **Seeds:** 10 per cell
- **Wall time:** 69.6s

## Results

| Temperature | γ (attractor weight) | Distinct paths | Paths observed |
|---:|---:|---:|---|
| 0.0 | 0.0 | 1 | `path:A` |
| 0.0 | 0.5 | 1 | `path:B` |
| 0.7 | 0.0 | 1 | `path:A` |
| 0.7 | 0.5 | 1 | `path:B` |
| 1.0 | 0.0 | 1 | `path:A` |
| 1.0 | 0.5 | 1 | `path:B` |

## Interpretation

Compare γ=0 (no LPSF) vs γ=0.5 (LPSF on path:B) at each temperature:

- **γ=0 high-temp distinct > γ=0.5 high-temp distinct** → LPSF reduces variance under LLM noise.
  The 'attractor as anchor in stochastic LLM' thesis, now properly testable.
- **γ=0 and γ=0.5 give same distinct count** → Attractor doesn't help against current LLM noise level.
  Either the attractor depth is too small relative to LLM vote, or the model is too consistent.
- **γ=0 distinct = 1 even at temp=1.0** → Haiku/Sonnet pairwise voting is robust to temperature.
  We'd need to either crank β much higher or use a smaller/weaker model.

Whatever the result, this is the first experiment where LLM temperature actually has
a causal path to selected_path. The earlier temperature sweep (with plain LLMPlusLPSF)
could not produce variance because LLM output was architecturally decoupled from selection.