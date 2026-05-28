# PLANS.md — Execution Plan Template for LPSF

Codex should use this file as the main execution-plan format when working in `/plan` or `/goal` mode.

## 1. Objective

State the concrete objective, not the whole dream.

Example:

```text
Implement LPSF-v0.1 graph-based prototype that shows experience-induced landscape change across at least three before/after experiments.
```

## 2. Scope

In scope:

- Repo scan.
- 2nd brain inventory scan if path is available.
- Safe note drafting under approved folder.
- Landscape state model.
- Plasticity operators.
- Hypothesis/collapse trace logging.
- Baseline comparison.
- Experiment reports.

Out of scope for v0.1:

- Training a foundation model.
- Direct hidden-state manipulation of proprietary LLMs.
- Literal quantum computing.
- Production deployment.
- Modifying existing 2nd brain notes.

## 3. Inputs

- This markdown pack.
- Uploaded hypothesis: state-space landscape plasticity.
- Existing repo files.
- Optional 2nd brain directory.
- Optional literature notes.
- User constraints.

## 4. Milestones

### M0 — Context Capture

Deliverable:

```text
ops/lpsf/PROJECT_CONTEXT.md
```

Must include:

- Repo structure.
- Build/test commands.
- Current code patterns.
- Existing memory/RAG files.
- Missing dependencies.
- 2nd brain path/access status.

### M1 — Theory Normalization

Deliverable:

```text
docs/lpsf/LPSF_SPEC.md
```

Must include:

- Definitions.
- Operator set.
- Memory policy.
- Evaluation hypotheses.

### M2 — Storage Layer

Deliverable:

```text
src/... landscape state storage OR docs-only schema if no codebase exists
```

Must include:

- experience_events
- concept_nodes
- semantic_edges
- plasticity_marks
- hypothesis_traces
- evaluation_runs

### M3 — Plasticity Operators

Implement or specify:

- deepen_attractor
- weaken_attractor
- open_path
- inhibit_path
- tilt_value_field
- modulate_sensitivity
- remap_schema
- reconsolidate_memory

### M4 — Experiments

Run or prepare:

- Attractor deepening experiment.
- RAG-vs-LPSF response shift experiment.
- Path opening experiment.
- Optional value tilt and forgetting experiments.

### M5 — Evaluation Report

Deliverable:

```text
experiments/lpsf/EVALUATION_REPORT.md
```

Must include:

- Baselines.
- Prompts.
- Outputs.
- Scoring rubric.
- Failures.
- Next steps.

## 5. Validation Commands

Codex must discover actual commands. If none exist, propose minimal commands.

Template:

```bash
python -m pytest
python -m lpsf.experiments.run --suite v0_1
python -m lpsf.evals.compare --baseline rag --candidate lpsf
```

## 6. Stop Conditions

Stop when:

- The v0.1 done definition is met.
- A sensitive-data or permission boundary is encountered.
- Installing packages or accessing external services requires approval.
- The repo lacks enough context to continue safely.

