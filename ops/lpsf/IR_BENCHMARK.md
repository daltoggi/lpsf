# LPSF IR Benchmark

_Generated 2026-05-28T16:27:44Z_

## Honest framing

LPSF is a **personalization prior**, not a generic relevance booster. So
this benchmark measures three different things, and a single 'LPSF score'
would be misleading:

1. **β upside** — does the LLM-judge rerank beat BM25?
2. **γ upside (aligned)** — does a prior over relevant-but-buried docs lift recall?
3. **γ risk (misaligned)** — how much does a *wrong* prior cost?

The corpus is **synthetic** (bigger, not real): 64 docs, 8 labeled queries, heavy cross-topic vocabulary bleed so BM25 is imperfect. This yields real
metrics and relative deltas, NOT external validity.

## Results (averaged over queries; metrics @5; deltas vs BM25)

| Condition | nDCG@5 | MRR | recall@5 |
|---|---:|---:|---:|
| A. BM25 only (baseline) | 0.859 (+0.000) | 1.000 (+0.000) | 0.516 (+0.000) |
| B. + aligned attractor | 1.000 (+0.141) | 1.000 (+0.000) | 0.625 (+0.109) |
| C. + misaligned attractor | 0.277 (-0.581) | 0.250 (-0.750) | 0.250 (-0.266) |
| D. + LLM-judge rerank | 0.830 (-0.029) | 1.000 (+0.000) | 0.500 (-0.016) |
| E. + rerank + aligned | 0.832 (-0.027) | 1.000 (+0.000) | 0.500 (-0.016) |

## Observed findings (this run)

- **Aligned prior helped**: recall@5 +0.109, nDCG@5 +0.141. The prior pulled relevant-but-buried docs up.
- **Misaligned prior hurt a lot**: nDCG@5 -0.581, MRR -0.750. A wrong prior is far more damaging than a right prior is helpful — the upside is bounded by the ceiling, the downside is not.
- **LLM-judge rerank did not help**: nDCG@5 -0.029. On synthetic bag-of-words summaries the judge has no real semantic signal to exploit; this is an honest null/negative result, not a tuned win.
- **Rerank caps recall**: rerank conditions only see the top-6 shortlist (pairwise is O(k²)), so they cannot rescue relevant docs buried below it the way the full-pool aligned attractor can. This is why E < B on recall — a structural property of pairwise reranking, not a bug.

## How to read this

- **B (aligned) vs A**: this is the personalization upside. A positive recall@5
  delta means the prior pulled relevant-but-buried docs into the top 5 — exactly
  what 'the user has engaged with these notes before' should do.
- **C (misaligned) vs A**: this is the risk. A negative delta is the cost of a
  bad prior. It should be clearly negative — that's the honest warning label.
- **D (rerank) vs A**: the classic reranking question. On synthetic bag-of-words
  summaries the LLM judge may help little or none; a null result here is itself
  honest information (the judge needs real semantic content to add value).
- **E vs D**: whether personalization stacks on top of reranking.

_Total cost: $0.0000. Wall: 0.4s. All conditions._

Reproduce: `python3 scripts/gen_eval_corpus.py && python3 scripts/build_corpus.py --corpus data/eval_corpus --db data/eval_corpus.fts.db && python3 scripts/ir_benchmark.py`