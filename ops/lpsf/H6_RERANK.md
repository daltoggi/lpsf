# H6 Adversarial under LLM-as-Reranker

_Generated 2026-05-26T11:57:44Z_

## Question

The original H6 showed that an attractor on `path:ev:wrong` (RAG=0.20, depth=0.8)
overrode `path:ev:correct` (RAG=0.90) under the plain LLMPlusLPSF baseline.
That worked because LLM output text was decoupled from selection.

Now LLMPlusLPSFRerank adds the LLM as a pairwise judge with its own system prompt.
We hold the attractor at the maximum legal strength (1.0) and sweep β (the weight
on the LLM judgment channel) to find where LLM rerank starts saving the correct answer.

## Setup

- **Model:** claude-haiku-4-5
- **Baseline:** LLMPlusLPSFRerank with α=1.0, γ=1.0, β ∈ [0.0, 0.3, 0.6, 1.0, 2.0]
- **Judge LLM:** same model, PAIRWISE_JUDGE_PROMPT system prompt
- **Fixture:** H6 — ev:correct (RAG 0.90), ev:wrong (RAG 0.20)
- **Attractor:** deepen path:ev:wrong with strength=1.0 (max legal)
- **Seeds:** 5 per cell
- **Wall time:** 10.3s

## Results

Cell shows the fraction of seeds where LPSF overrode (selected `path:ev:wrong`).
0/N = LLM judge saved the correct answer. N/N = attractor still dominated.

| β (LLM weight) | T=0.0 wrong-wins | T=1.0 wrong-wins |
|---:|---:|---:|
| 0.00 | 5/5 | 5/5 |
| 0.30 | 0/5 | 0/5 |
| 0.60 | 0/5 | 0/5 |
| 1.00 | 0/5 | 0/5 |
| 2.00 | 0/5 | 0/5 |

## Interpretation

- **β=0.0** = plain LPSF (LLM judgment disabled). Expected: wrong always wins,
  reproducing the original H6 result.
- **β high enough** = LLM judge wins. The β threshold at which the judge starts
  protecting against the attractor is the operational tradeoff knob.

## Amplitude math (for reference)

    amp(correct) = α*0.90 + β*1   + γ*0      = 0.90 + β
    amp(wrong)   = α*0.20 + β*0   + γ*1.0    = 1.20

Judge always picks correct ⇒ correct wins iff `0.90 + β > 1.20` ⟺ `β > 0.30`.

So we predict the flip happens at **β ≈ 0.30**: below that, attractor dominates;
above, LLM judge saves the correct answer.