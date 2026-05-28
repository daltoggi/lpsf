# Codex Goal — LPSF-v0.1

Copy/paste the block below into Codex after `/plan` has produced a safe plan.

```text
/goal Build LPSF-v0.1 as an inspectable graph/state prototype, not a new foundation model, using the project rules in AGENTS.md and PLANS.md. First read README.md, AGENTS.md, PLANS.md, docs/01_LPSF_THESIS.md, docs/02_ARCHITECTURE.md, docs/03_PLASTICITY_OPERATORS.md, docs/04_MEMORY_FORGETTING.md, docs/05_DB_SCHEMA.md, second_brain/2ND_BRAIN_PROTOCOL.md, and experiments/EXPERIMENT_PLAN.md. Then inspect the repo and create ops/lpsf/PROJECT_CONTEXT.md and ops/lpsf/STATUS_LOG.md. If SECOND_BRAIN_DIR is configured, scan it read-only and create a sanitized 2nd brain inventory summary; do not modify existing notes and write drafts only under an approved LPSF draft folder. Implement or scaffold a persistent landscape_state with experience_events, concept_nodes, semantic_edges, attractors, plasticity_marks, hypothesis_traces, and collapse_traces. Implement the eight plasticity operators or the smallest tested stubs if the repo is not ready. Create at least three before/after experiments comparing LLM-only or RAG/static-memory behavior against LPSF state-change behavior. Produce an evaluation report with failures, risks, and next steps. Stop only when the v0.1 done definition is met, or pause if you need permission for package installation, external services, sensitive 2nd brain access, file deletion/move, or writes outside approved paths.
```

## Done Definition

Codex should stop only when all are satisfied:

- `ops/lpsf/PROJECT_CONTEXT.md` exists.
- `ops/lpsf/STATUS_LOG.md` is updated.
- 2nd brain inventory summary exists or access-blocked note exists.
- LPSF spec is frozen or updated.
- Persistent landscape state schema exists.
- Plasticity operators exist as code or executable pseudocode with tests.
- At least three experiments are prepared or run.
- Baseline comparison exists.
- Evaluation report exists.
- No unsafe private raw data is committed.

