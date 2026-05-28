# LPSF Project Summary

_One-page handoff for anyone discovering this repo._
_Last updated: 2026-05-26._

## What this is

LPSF v0.1 is a **memory-conditioned reranking layer over RAG retrieval**.
It accumulates persistent prior weights on candidate paths through eight
update policies ("operators"), and uses those weights to deterministically
modify which candidate wins selection. It is NOT (yet) modifying LLM
internal reasoning, token sampling, or generation — only the choice among
already-retrieved candidates.

The entire mechanism collapses to one of two equations, depending on which
baseline you use:

```
LLMPlusLPSF:        c* = argmax_c [ r(c) + a(c) ]
LLMPlusLPSFRerank:  c* = argmax_c [ α·r(c) + β·ℓ(c) + γ·a(c) ]
```

where `r(c)` is the RAG score, `a(c)` is the accumulated attractor depth,
and `ℓ(c)` is the LLM judge's pairwise-comparison score. LLM output text
plays no role in selection unless β > 0.

## What was proven (six axes)

| Axis | Evidence | Cost |
|---|---|---|
| **Controllability** — LPSF can override RAG | H6 adversarial: 10/10 seeds, baselines diverge | $0.01 |
| **Predictability** — exact decision boundary `Δa > Δr` | Rank-flip frontier: 56/56 cells match prediction | $0 |
| **Reversibility (operator)** — bias undoable by counter-experience | H7: deepen → weaken reverses → competing deepen overrides | $0 |
| **Tunability** — β knob trades attractor autonomy vs LLM-judge safety | H6 β-sweep: predicted threshold β > 0.30 confirmed exactly | $0.002 |
| **Real-corpus behaviour** — same equation works on real BM25 input | 4-query eval over markdown FTS corpus: 2/4 scenarios flip as predicted | $0.023 |
| **Reversibility (decay)** — bias naturally decays with `half_life` | H8: 3 half-lives flips selection back; selector now honors decay rows | $0 |

**Total experimental cost across the entire project: ~$0.22.**

## What is NOT yet proven (do not overclaim)

- "LLM internal plasticity" — selection is decoupled from LLM reasoning even in the rerank baseline; the LLM is just one weighted term.
- "Broad real-world generalization" — corpus is 6 documents. Larger / noisier / domain-specific corpora untested.
- "Operators model distinct learning rules" — all 8 operators are different policies on a single `attractor_depth` field. Diversity is in *how* depth changes, not *what* gets computed.
- "Always improves correctness" — H6 shows LPSF can override RAG with a miscalibrated prior. The rerank channel (β) mitigates this but doesn't eliminate it.

## How to reproduce

```bash
# Clone and install
pip install -e .

# Run the full test suite (no API keys required for mocks)
python3 -m pytest -q     # 188 tests, ~15s, $0

# Build the FTS corpus index (deterministic, gitignored)
python3 scripts/build_corpus.py

# Run the mock-only standard benchmark
python3 scripts/run_benchmark.py --mode smoke --dry-run

# Run the real-API benchmark (requires ANTHROPIC_API_KEY in .env.local)
python3 scripts/run_benchmark.py --mode standard       # ~$0.26
python3 scripts/rank_flip_frontier.py                  # $0
python3 scripts/temperature_sensitivity.py             # ~$0.04
python3 scripts/h6_with_rerank.py                      # ~$0.002
python3 scripts/depth_sweep.py                         # $0 (cache hits)
python3 scripts/real_corpus_eval.py                    # ~$0.023

# Regenerate the markdown evaluation report from the existing JSON ($0)
python3 scripts/regenerate_report.py
```

## Repo layout

```
data/corpus/                 6 markdown notes (read-only RAG substrate)
data/corpus.fts.db           SQLite FTS5 index (gitignored, rebuilt by script)
docs/lpsf/CURRENT_STATUS.md  Canonical honest positioning
docs/lpsf/LPSF_SPEC.md       Theoretical aspiration (read as direction, not as code description)
src/lpsf/
  db.py, schema.sql          13-table SQLite storage
  operators/                 8 update policies + decay
  experiments/
    baselines.py             Selection equations live here
    claude_llm.py / openai_llm.py / codex_llm.py
    local_fts_rag.py         Read-only adapter over the FTS index
    hypotheses/h1..h8.py     Eight falsifiable scenarios
    benchmark.py / report.py / cost.py
scripts/                     Reproducible experiment runners
ops/lpsf/                    Generated reports + STATUS_LOG
tests/                       188 tests, all deterministic
```

## Key reports

- `ops/lpsf/EVALUATION_REPORT.md` — auto-generated benchmark across H1/H3/H4/H5
- `ops/lpsf/ADVERSARIAL_RESULTS.md` — H6 controllability
- `ops/lpsf/RANK_FLIP_FRONTIER.md` — exact decision boundary
- `ops/lpsf/RECONSOLIDATION_RESULTS.md` — H7 reversibility
- `ops/lpsf/H6_RERANK.md` — H6 under LLM-as-judge (tunability)
- `ops/lpsf/REAL_CORPUS_EVAL.md` — end-to-end on real markdown
- `ops/lpsf/STATUS_LOG.md` — full session-by-session record

## One-line public claim

> LPSF v0.1: a controllable, predictable, reversible, tunable
> memory-conditioned reranking layer over RAG retrieval —
> verified end-to-end across synthetic fixtures and a small
> real markdown FTS corpus. Decision boundary Δa > Δr exactly.
> β knob trades attractor autonomy against LLM-judge safety
> at a computable threshold. Bias is reversible both by
> explicit operator calls and by time-based decay.

## Open follow-ups (not core gaps)

- Larger / domain-specific RAG corpora
- Listwise reranker (current is pairwise; affects scale to k>10 candidates)
- LLM-as-judge prompt sensitivity audit (current is one short directive prompt)
- Operator registry extension so `apply_decay` can be invoked via `run_experiment` scenarios
- Latency / quality study at production scale

## License & data

All experimental data is synthetic. The `data/corpus/*.md` notes are
hand-written generic technical writing; no personal or sensitive content
appears in any committed file. `.env.local` is gitignored; API keys never
enter source or reports.
