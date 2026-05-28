# LPSF — Current Implementation Status

_Last updated: 2026-05-26_

This document is the **canonical honest summary** of what LPSF v0.1 actually
is in code, as distinct from the broader theoretical vision in `LPSF_SPEC.md`,
`01_LPSF_THESIS.md`, and the original README pack.

If you only have 60 seconds, read just the One-Line Summary and the
Selection Equation. The rest is justification.

---

## One-Line Summary

> **LPSF v0.1 is a memory-conditioned reranking layer over RAG retrieval.**
>
> It accumulates persistent prior weights on candidate paths through 8 update
> policies ("operators"), and uses those weights to deterministically modify
> which candidate wins selection. It does NOT (yet) modify LLM internal
> reasoning, token sampling, or generation in any direct way.

## Two Tracks

- **Reranking track (v0.1, published):** the hosted-API LPSF described in this
  document — a memory-conditioned reranking layer. Honest ceiling: it can never
  write memory into parameters, because you cannot touch a hosted model's weights.
- **Substrate track (new):** memory that lives in parameters, not in the context.
  - `src/lpsf/substrate/` — a numpy mechanism demo that passes the falsifiable
    "empty-context recall" test and quantifies the fixed-dimension capacity
    ceiling (dense ≪ sparse ≪ expandable).
  - **Real-model result:** the same test PASSES on Qwen2.5-0.5B via
    LoRA-from-experience — base model recalls a taught fictional fact with empty
    context at 0.00 → LoRA at 1.00 on held-out phrasings
    (`ops/lpsf/LORA_MEMORY.md`). Memory written into the weights of a real
    transformer; the thing a hosted-API + RAG stack structurally cannot do.
  - Honest scope (see [`SUBSTRATE_NOTES.md`](SUBSTRATE_NOTES.md)): one fact, a
    0.5B model; does not yet address catastrophic forgetting, interference, or
    scaling. This is the first concrete step toward the project's actual
    ambition (true memory), which the reranking track structurally cannot reach.

## It Is Now Also a Tool (not just a framework)

`src/lpsf/app/` + `scripts/lpsf_search.py` turn the harness into a usable
personalizing search CLI. Each user `pick` is recorded as an
`experience_event` that deepens an attractor, persisted on disk. Repeated
picks raise a note's rank on future related queries. This is the honest,
scoped realization of the original "landscape changes after experience"
vision — the *landscape* is the reranking prior, the *experience* is real
usage. See `ops/lpsf/PERSONALIZATION_DEMO.md`.

## Selection Equation

There are now **two** selection equations, one per baseline:

**`LLMPlusLPSF`** (original, LLM-decoupled):
```
c* = argmax_c [ rag_score(c) + attractor_depth(c) ]
```
LLM output text plays no role in selection. Path is deterministic given
(retrieval state, attractor state).

**`LLMPlusLPSFRerank`** (added in Phase D — LLM judgment in the loop):
```
c* = argmax_c [ α·rag_score(c) + β·llm_rank(c) + γ·attractor_depth(c) ]
```
Where `llm_rank(c)` ∈ [0, 1] comes from pairwise LLM voting using
PAIRWISE_JUDGE_PROMPT. With β > 0 the LLM **does** affect path selection;
β acts as a tunable knob for "how much should LLM judgment override LPSF state".

A path B overrides path A iff:

```
attractor_depth(B) − attractor_depth(A)  >  rag_score(A) − rag_score(B)   (plain)
γ·Δa  >  α·Δr + β·Δℓ                                                       (rerank)
```

Both are falsifiable cores. Every experimental result follows from them.

---

## What Has Been Proven (✓)

| Property | Evidence | Confidence |
|---|---|---|
| **Controllability**: LPSF attractor can override RAG rankings | H6 adversarial, 10/10 across haiku seeds; LLMPlusRAG and LLMPlusLPSF diverge consistently | High |
| **Predictability**: Empirical decision boundary matches `argmax(r + a)` exactly | Rank-flip frontier: 56/56 cells on the Δa = Δr diagonal | High |
| **Reversibility**: A deepened bias can be reversed by counter-experience | H7 reconsolidation: deepen → weaken reverses → competing deepen overrides; 5/5 tests | High |
| **Tunability**: An LLM-as-judge channel (β) provides a safety net against miscalibrated attractors | H6-with-rerank: predicted β > 0.30 threshold confirmed exactly (5/5 wrong-wins at β=0, 0/5 from β=0.30 onward) | High |
| **Real-corpus behaviour**: Same selection equation applies on actual BM25 ranking | Real-corpus eval over 6 markdown notes: LPSF flips RAG winner when prior aligns; LLM judge rescues correct answer when prior is miscalibrated (`REAL_CORPUS_EVAL.md`) | Medium (small corpus) |
| **Decay-driven reversibility**: `half_life` produces time-based natural weakening | H8 reconsolidation by decay: after 3 half-lives, effective depth drops below the RAG margin and selection flips back. Required a `_load_attractors` fix that honors decayed rows (previously decay was log-only) | High |
| **Real-index plumbing**: adapter retrieves + gates + feeds baselines on a real personal FTS index | Brain smoke test over a 529-note index: all notes pass the sensitivity gate, 4/4 queries retrieve, LLM-judge rerank diverges on 1/4. Read-only, sensitivity-gated, no content written to repo (`BrainBackroomRag`, gitignored `BRAIN_SMOKE.md`) | Medium (plumbing, not quality) |
| **Reproducibility**: Same (snapshot, seed) → same selected_path | H4 standard run, 80/80 across claude-sonnet-4-5 + gpt-4o | High |
| **Baseline independence**: LLMPlusRAG ignores attractor state by design | Verified mechanistically + empirically (H6) | High |
| **Safety isolation**: anthropic/openai SDKs not loaded by `import lpsf.experiments`; subprocess gated to codex_llm.py | Two negative regression tests | High |
| **Harness reliability**: deterministic, repeatable, file-cached for free re-runs | 171 passing tests, full re-render from JSON costs $0 | High |

## What Is NOT Yet Proven (✗ — do not overclaim)

| Claim | Reality | Why |
|---|---|---|
| "LPSF makes LLM reasoning plastic" | Not demonstrated | Even in the rerank baseline, LLM output is *one weighted term*, not internal reasoning modification |
| "Generalizes to broad real-world corpora" | Partial only | Real BM25 tested on a 6-doc demo corpus (`REAL_CORPUS_EVAL.md`) and a 64-doc labeled synthetic set with nDCG/MRR/recall (`IR_BENCHMARK.md`). The corpora are still synthetic — bigger, not real. External validity on real domain corpora remains open. |
| "Personalization is free upside" | Refuted — it's asymmetric | IR benchmark: an *aligned* prior lifts nDCG@5 by +0.14 and recall@5 by +0.11; a *misaligned* prior drops nDCG@5 by −0.58 and MRR by −0.75. A wrong prior hurts far more than a right one helps. LLM-judge rerank was null (−0.03) on synthetic bag-of-words summaries. |
| "Different operators model different learning rules" | Misleading framing | All 8 operators are update policies on a single `attractor_depth` field; the diversity is in *how* depth changes, not *what* changes |
| "Correctness benefit" | Open | Rerank H6 shows LLM judge protects against bad attractors; but LPSF can also *cause* bad selections if attractor is wrong AND β is low |

---

## Honest Positioning vs Prior Work

The closest existing literature, and how LPSF v0.1 actually fits:

- **RAG** (Lewis et al., 2020): external non-parametric memory at retrieval time.
  LPSF does *not* re-invent RAG; it sits *after* RAG, modifying the selection
  among the candidates that RAG returned.
- **Reranking** (BEIR, late interaction, etc.): a separate post-retrieval scoring
  stage. LPSF is best read as a **persistent-state reranker**, where the
  reranking weights accumulate over time via operator calls instead of being
  recomputed from query/document features alone.
- **Pairwise Ranking Prompting (PRP)** (Qin et al., 2023): uses LLMs as
  rankers. LPSF currently does *not* do this — its `β` coefficient on
  LLM-derived ranking signal is effectively zero. The natural next step is
  to add an LLM-as-reranker channel (`s(c) = α·r(c) + β·ℓ(c) + γ·a(c)`).
- **Memory-augmented LLMs / continual learning**: the aspiration. The
  current implementation is a long way short of this — but the persistent
  attractor field is a defensible mechanistic substrate to build toward it.

## What the Operators Actually Do

All eight operators (`deepen`, `weaken`, `inhibit`, `open`, `tilt`, `modulate`,
`remap`, `reconsolidate`) write rows into `plasticity_marks` and update
`attractors.depth`. They differ in:

1. **Sign and magnitude** of the depth delta.
2. **Target** (path id vs axis vs schema vs sensitivity profile).
3. **Decay parameters** (half_life, threshold).
4. **Append-only invariants** preserved via triggers.

They do **not** differ in *what kind of computation* LPSF performs at
selection time. That computation is always `argmax(r + a)`.

This is fine — it's a clean substrate. But describing the operators as if
they implemented Hebbian learning, attention reweighting, or memory
consolidation independently *would* be overclaiming.

---

## The Experimental Record (Compact)

| Experiment | What It Tested | Result | Honest Interpretation |
|---|---|---|---|
| M4 P1 mock | Harness plumbing | 46/46 pass | Engineering soundness |
| M4 P2 Codex | Real LLM via OAuth | 11/11 pass | Works with real models |
| M4 P3 standard | claude-sonnet-4-5 + gpt-4o, H1/3/4/5 × 10 seeds | 80/80 pass, $0.26 | Confirms harness; doesn't prove generalization |
| Temperature sensitivity | Does temp change path? | No, at any temperature 0.0–1.0 | Architectural, not surprising — LLM noise doesn't enter selection |
| Depth sweep | Find noise-tolerance threshold | No threshold found (all depths converge) | H4 fixture is too easy; need tied-score fixture |
| **H6 adversarial** | **Can LPSF override RAG rankings?** | **Yes, 10/10 every seed** | **The single meaningful independence result** |

## Cost-to-Date

About **$0.40** total in paid API calls across all M4 Phase 3 and
follow-up experiments. Re-runs are free due to SHA-256 file caching.

---

## Where to Go Next (Ordered by Information / Cost)

1. **Rank-flip frontier** (Phase B, planned): Δr × Δa heatmap to draw the
   actual decision boundary. ~$0, highest info gain at this stage.
2. **Reconsolidation test (H7)**: deepen then reverse. Validates that the
   "plasticity" name has substance. ~$0.
3. **LLM-as-reranker**: introduce `β·ℓ(c)` channel. Lets temperature actually
   matter for selection. Code change + ~$0.30 for re-benchmark.
4. **Real RAG adapter**: read-only over an external knowledge snapshot.
   Removes the synthetic-fixture caveat. Largest engineering cost.

## How to Read This Repo Going Forward

- `docs/lpsf/CURRENT_STATUS.md` (this file): what's actually built.
- `docs/lpsf/LPSF_SPEC.md`: the theoretical aspiration. Read as research
  direction, not as a description of `src/`.
- `ops/lpsf/STATUS_LOG.md`: chronological session record (mostly accurate;
  some early entries used the over-strong "dominance" framing — corrected
  in later entries).
- `ops/lpsf/EVALUATION_REPORT.md`: the auto-generated benchmark output.
  Has its own "Scope of claims" section.
- `ops/lpsf/ADVERSARIAL_RESULTS.md`: the most important single result.
