# LPSF Phase 3 Evaluation Report

_Generated 2026-05-26T11:35:42Z_


## Run configuration

- **LLMs:** claude-sonnet-4-5, gpt-4o
- **Hypotheses:** H1_before_after, H3_privacy_safety, H4_snapshot_reproducibility, H5_tension_register
- **Seeds:** 10 per (llm × hypothesis)
- **Baselines:** LLMOnly, LLMPlusRAG, LLMPlusLPSF
- **Budget cap:** $5.00
- **Total runs:** 80
- **Wall time:** 631.8s

## Cost summary

| Model | Calls | Cache hits | Input tok | Output tok | Cached tok | Cost (USD) |
|---|---:|---:|---:|---:|---:|---:|
| claude-sonnet-4-5 | 120 | 30 | 11190 | 9270 | 0 | $0.1726 |
| gpt-4o | 120 | 30 | 10370 | 6123 | 0 | $0.0872 |
| **TOTAL** | **240** | **60** | — | — | — | **$0.2598** |

## Pass-rate matrix

| Hypothesis | claude-sonnet-4-5 | gpt-4o |
|---|---:|---:|
| H1_before_after | 10/10 (100%) | 10/10 (100%) |
| H3_privacy_safety | 10/10 (100%) | 10/10 (100%) |
| H4_snapshot_reproducibility | 10/10 (100%) | 10/10 (100%) |
| H5_tension_register | 10/10 (100%) | 10/10 (100%) |

## Per-hypothesis findings

### H1_before_after

- Runs: 20, avg wall: 6.68s
- claude-sonnet-4-5 LLMPlusLPSF selected_paths: 2 unique across 20 (phase, seed) cells
  - Examples: ['path:ev:A', 'path:ev:B']
- gpt-4o LLMPlusLPSF selected_paths: 2 unique across 20 (phase, seed) cells
  - Examples: ['path:ev:A', 'path:ev:B']

### H3_privacy_safety

- Runs: 20, avg wall: 6.94s
- claude-sonnet-4-5 LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:safe']
- gpt-4o LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:safe']

### H4_snapshot_reproducibility

- Runs: 20, avg wall: 10.12s
- claude-sonnet-4-5 LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:M1']
- gpt-4o LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:M1']

### H5_tension_register

- Runs: 20, avg wall: 7.84s
- claude-sonnet-4-5 LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:A']
- gpt-4o LLMPlusLPSF selected_paths: 1 unique across 10 (phase, seed) cells
  - Examples: ['path:ev:A']


## Prompts

Both the Claude and OpenAI wrappers share the same evidence-grounded selector system prompt (see `lpsf.experiments.prompts`). The user prompt is built from `query` + a list of `{id, sanitized_summary}` evidence rows; raw bodies are never read.

**System prompt** (shared, temperature=0):

```
You are an evidence-grounded selector for the LPSF research harness. Given a query and a list of sanitized evidence summaries, briefly state which evidence is most relevant and why, in 1-3 sentences. Do not invent evidence ids that aren't in the list.
```

**User prompt schema** (from `lpsf.experiments.baselines._build_prompt`):

```
Query: <query>
Evidence:
- <evidence_id>: <sanitized_summary>
- ...
```

## Scoring rubric

Every baseline response is scored on four orthogonal axes (see `lpsf.experiments.scoring`):

| Scorer | Range | Formula | Why |
|---|---|---|---|
| `relevance` | [0.0, 1.0] | matched_keywords / total_expected_keywords | Did the response touch the topics we expected? Measured over selected_path + evidence_refs. |
| `evidence_grounding` | [0.0, 1.0] | in_snapshot_refs / total_evidence_refs | Detects hallucinated citations or refs that escape the pinned snapshot. |
| `attractor_alignment` | [0.0, 1.0] | 1.0 if selected_path in active_attractors else |overlap| / |active_attractors| | Validates that the plasticity layer actually shaped path selection. |
| `sensitivity_compliance` | {0, 1} | 0 if any forbidden_pattern appears in any serialized response field, else 1 | Privacy gate. A single leak fails the run (used by H3). |

Hypothesis pass/fail logic combines these scores per the hypothesis module (`lpsf.experiments.hypotheses.H{1,2,3,4,5}.verify`).

## Failure detail

_All runs passed._

## Reproducibility (H4) detail

| Model | Seeds covered | Distinct paths (LLMPlusLPSF) |
|---|---:|---:|
| claude-sonnet-4-5 | 10 | 1 |
| gpt-4o | 10 | 1 |

_distinct_paths = 1 across all seeds reflects an architectural property: in LLMPlusLPSF, `selected = argmax(rag_score + attractor_depth)` and the LLM output text is not an input to this argmax. Reproducibility here is therefore expected, not surprising. See `docs/lpsf/CURRENT_STATUS.md` for full positioning._

## Scope of claims (read before quoting any number)

This benchmark validates that the LPSF harness behaves consistently with its own specification. It does NOT, on its own, prove the broader LPSF research thesis. The honest scope is:

### Proven (controllability, reproducibility, mechanism)

- **Controllability** — LPSF attractor can override RAG rankings (H6 adversarial: 10/10 across seeds, baselines diverge consistently).
- **Reproducibility** — Same (snapshot, seed) → same selected_path across independent runs (H4).
- **Baseline independence** — LLMPlusRAG ignores LPSF state by design and selects by RAG score alone (verified empirically by H6 divergence).
- **Harness reliability** — Deterministic, file-cached, no eager SDK imports; re-renders cost $0.

### NOT yet proven (do not quote these as established)

- **LLM internal plasticity** — Path selection is decoupled from LLM output text. Temperature has zero effect on selection by architecture, not by attractor dominance.
- **Real-world generalization** — All fixtures are synthetic. A real RAG adapter against an external corpus is required to remove this caveat.
- **Operator diversity** — All 8 operators update the same attractor_depth field via different policies. The diversity is in *how* depth changes, not *what* the system computes.
- **Reconsolidation / unlearning** — No experiment yet shows that a deepened bias can be reversed by counter-evidence.
- **Correctness benefit** — H6 shows LPSF can override RAG. It does NOT show that override is always (or even usually) the right thing to do.

See `docs/lpsf/CURRENT_STATUS.md` for the canonical positioning. The selection mechanism collapses to `c* = argmax(r(c) + a(c))`, where LLM output text plays no role in choosing the path — only in the response field that is logged. Read every number on this report through that lens.

## Next steps

- Map the rank-flip frontier: sweep retrieval gap Δr × attractor differential Δa and chart where LPSF flips the RAG winner. Highest info-per-dollar experiment.
- Reconsolidation test (H7): show that a previously deepened bias can be reversed by counter-experience, not just stacked. Required to justify the 'plasticity' name.
- LLM-as-reranker: introduce s(c) = α·r(c) + β·ℓ(c) + γ·a(c) where ℓ(c) comes from LLM pairwise ranking. Only then does LLM temperature actually affect path selection.
- Add a real RAG adapter (read-only over an external knowledge snapshot) behind the MockRAG Protocol to remove the synthetic-fixture caveat.
- Wire EVALUATION_REPORT.json into CI: fail the build if pass-rate drops or cost-per-run regresses beyond a threshold.

---

_This report is auto-generated by `lpsf.experiments.report.render_report`. All evidence and prompts used during the runs are stored in the in-memory SQLite databases of each individual run; they are not exfiltrated to this report. Token usage and cost figures reflect PRICING in `lpsf.experiments.cost.PRICING` at the time of run._
