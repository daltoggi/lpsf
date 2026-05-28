# LPSF M4 — Experiment Harness (Phase 1 + Phase 2)

Validates the operator → trace → evaluation flow end-to-end. Three phases
were planned:

- **Phase 1 (shipped)** — Mock-only. Deterministic `MockLLM` + `MockRAG`.
  No network. $0 cost. <1s runtime per test. Verifies harness plumbing.
- **Phase 2 (shipped)** — Codex CLI wrapper. Real LLM via subprocess to
  `~/.bard-harness/scripts/call-model.sh codex`. $0 per call (ChatGPT Plus
  OAuth). File-cached so repeat runs are free. Verifies behavior with a
  real model.
- **Phase 3 (deferred)** — Claude / OpenAI API. Quantitative benchmark.
  Cost will be calculated and reported BEFORE any launch.

## What's here

| File | Purpose |
|---|---|
| `mock_llm.py` | Deterministic LLM stub. `complete(prompt, context)` returns a stable response derived from a SHA-256 of `(prompt, context, seed)`. |
| `mock_rag.py` | `EvidenceAdapter`-compliant fixture-driven retrieval. Strips bodies; returns only `id / score / sanitized_summary / source_type`. |
| `codex_llm.py` | **Phase 2.** Real LLM via Codex CLI subprocess. Same surface as MockLLM. Caches responses by SHA-256 of `(prompt, context, model_id)` under `~/.cache/lpsf/codex_llm/`. |
| `scoring.py` | Four pure scoring functions: relevance, evidence_grounding, attractor_alignment, sensitivity_compliance. |
| `baselines.py` | `Response` dataclass + four baselines: `LLMOnly`, `LLMPlusRAG`, `LLMPlusStaticMemory`, `LLMPlusLPSF`. |
| `runner.py` | `run_query` (one query → writes hypothesis_traces + collapse_traces) and `run_experiment` (full scenario → writes evaluation_runs). |
| `scenarios.py` | Synthetic snapshot/event helpers + `default_rag_fixture` shared across hypotheses. |
| `hypotheses/h1`…`h5` | Each module exposes `build_scenario(snapshot_id, event_id)` and `verify(result)`. |

## Contracts

- **No network.** No module imports `requests`, `httpx`, `urllib.request`, `anthropic`, `openai`, or `socket`.
- **No catalog-engine.** No module imports `catalog_engine` or touches `/Users/.../2nd brain/`.
- **No real LLM.** `MockLLM` is fully deterministic; same `(prompt, context, seed)` → same output.
- **No body leakage.** `MockRAG.retrieve()` projects only sanitized fields; if a fixture carries a `body` key, it is dropped.
- **Append-only respected.** Runner writes via INSERT; never UPDATEs marks/events/traces.

## Swapping LLMs

The baseline + runner contract is LLM-agnostic. Three concrete LLMs:

```python
from lpsf.experiments import MockLLM, CodexLLM   # Phase 1 / Phase 2
# Phase 3 will add ClaudeLLM, OpenAILLM with the same surface

llm = MockLLM(seed=42)                # deterministic, $0
llm = CodexLLM()                      # real LLM, $0, OAuth-backed
# llm = ClaudeLLM(...)                # Phase 3, cost-bearing
```

All three return `{response, confidence, evidence_refs, model}` from
`complete(prompt, context=...)`. The runner does not know which is in use.

The `EvidenceAdapter` Protocol allows the same kind of swap for retrieval
(`MockRAG` → a real catalog-engine adapter in a later phase).

### Phase 2 cache

`CodexLLM` writes one JSON file per unique `(prompt, context, model_id)`
under `~/.cache/lpsf/codex_llm/` (configurable via `cache_dir=`). The cache
is content-addressed and append-only: repeat runs read from disk and emit
zero subprocess invocations. Delete the cache directory to force fresh
calls.

## Running

```bash
python3 -m pytest tests/experiments/ -q
```

All tests use in-memory SQLite. Phase 1 runtime: <1s. Phase 2 adds one real
Codex call (cached after first run) plus mock-subprocess unit tests; full
suite runtime on first run is ~10-30s (one network-bound Codex call), <2s
on subsequent runs (cache hit).

To skip the real Codex smoke test (e.g. on a CI machine without
`~/.bard-harness`):

```bash
# CodexLLM.is_available() returns False if the script is missing,
# and the smoke test auto-skips.
```
