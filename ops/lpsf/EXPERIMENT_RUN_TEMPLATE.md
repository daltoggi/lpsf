# LPSF Experiment Run Template

Interpretation guide for one row of `evaluation_runs` produced by
`lpsf.experiments.runner.run_experiment`.

## What a "run" is

One run = one hypothesis (H1–H5) executed across one or more baselines on
one pinned snapshot.

- **suite_name** — the hypothesis name (e.g. `H1_before_after`).
- **candidate_name / baseline_name** — comma-joined baseline list.
- **snapshot_id** — FK into `evidence_snapshots`. Pin this for replay.
- **state_db_version** — `lpsf.db.STATE_DB_VERSION` at run time.
- **prompts** — JSON array of every prompt sent to the (mock) LLM during this run.
- **sanitized_outputs** — JSON array of per-(phase, baseline, query) outputs. Each entry includes `phase`, `baseline`, `query_id`, `selected_path`, `evidence_refs`, `score_components`, `warnings`, `model_version`.
- **score_summary** — JSON map: `{phase: {baseline: {score_component: value}}}`.
- **failures** — JSON array of `{source, detail}` items emitted by the hypothesis-specific `verify(result)`.
- **report_refs** — empty in Phase 1; Phase 3 will populate with paths to `EVALUATION_REPORT.md` excerpts.

## Reading `score_summary`

Four components per (phase, baseline):

| Component | Range | Meaning |
|---|---|---|
| `relevance` | 0.0–1.0 | Fraction of expected keywords present in `selected_path` or evidence summaries. |
| `evidence_grounding` | 0.0–1.0 | Fraction of `evidence_refs` actually in the snapshot's pool. 0 if no refs were emitted. |
| `attractor_alignment` | 0.0–1.0 | 1.0 if `selected_path` matches an active attractor; otherwise overlap fraction. |
| `sensitivity_compliance` | 0 or 1 | 1 = no forbidden pattern leaked into any field. Single binary gate. |

## Reading `failures`

Each item: `{"source": "verify", "detail": "<human-readable reason>"}`.
A run with empty `failures` and `passed=True` is a green run.

## Phase 2 swap (shipped)

To run with a real (free, OAuth-backed) Codex LLM:

```python
from lpsf.experiments import CodexLLM
llm = CodexLLM()  # subprocess wrapper around call-model.sh codex
run_experiment(conn, llm=llm, ...)
```

No other change required. Same Response shape, same trace writes, same
evaluation_runs row. First call to a unique (prompt, context) takes ~5-30s
(Codex CLI subprocess); subsequent calls are file-cache hits and free.

### Cost (Phase 2)

| Item | Cost |
|---|---|
| Per Codex call | $0 (ChatGPT Plus OAuth subscription) |
| Cache hit | $0, ~1ms |
| Wall time per fresh call | 5-30s |
| Cache location | `~/.cache/lpsf/codex_llm/<sha256>.json` |

Subscription required: ChatGPT Plus (or equivalent OAuth-backed tier on
the underlying provider). The harness does not bill on a per-call basis.

## Phase 3 swap (cost-bearing)

To run with Claude / OpenAI:

```python
from lpsf.experiments.claude_llm import ClaudeLLM
llm = ClaudeLLM(model="claude-3-5-sonnet-latest", api_key=os.environ["ANTHROPIC_API_KEY"])
```

**Cost note**: Phase 3 launch will be preceded by a cost calculation message
that estimates `(query_count × baseline_count × avg_tokens × price_per_token)`
for the requested hypothesis set. No Phase 3 run starts without explicit
user authorization.

## Snapshot pinning

Reproducibility requires the same snapshot_id. To replay a run:

1. Read `evidence_snapshots` for the original snapshot_id; recreate metadata.
2. Recreate the same RAG fixture (Phase 1) or pin the same catalog-engine
   snapshot (Phase 3).
3. Re-run with the same seed.

In Phase 1 the snapshot_id is the synthetic constant `snap_exp` (or whatever
the test fixture defines); in Phase 3 the snapshot_id is derived
deterministically from the adapter metadata via `lpsf.snapshot.pin_snapshot`.

## What this run is NOT

- Not an EVALUATION_REPORT. The report (Phase 3) aggregates multiple runs
  and presents human-readable findings.
- Not a benchmark. Phase 1 numbers are derived from deterministic mocks; they
  validate the harness, not the real model's behavior.
- Not authoritative for the M4 hypotheses themselves — Phase 1 confirms the
  state-machine plumbing; Phase 2/3 add real LLM variability that the
  hypotheses ultimately need to test.
