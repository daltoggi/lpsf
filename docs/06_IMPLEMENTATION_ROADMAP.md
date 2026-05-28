# 06 — Implementation Roadmap

## Phase 0 — Project Grounding

Goal:

Codex understands the repo, existing patterns, 2nd brain access status, and safe write boundaries.

Deliverables:

```text
ops/lpsf/PROJECT_CONTEXT.md
ops/lpsf/STATUS_LOG.md
second_brain_drafts/lpsf/2ND_BRAIN_INVENTORY_SUMMARY.md
```

Exit condition:

Codex can state what exists, what is missing, and where it may safely write.

## Phase 1 — Docs-Only Spec Freeze

Goal:

Create stable spec before coding.

Deliverables:

```text
docs/lpsf/LPSF_SPEC.md
docs/lpsf/OPERATOR_SPEC.md
docs/lpsf/MEMORY_POLICY.md
docs/lpsf/EVAL_SPEC.md
```

Exit condition:

Spec has no unresolved core contradiction.

## Phase 2 — Storage Prototype

Goal:

Represent landscape state persistently.

Deliverables:

```text
schema.sql or equivalent
seed data
state export/import
```

Exit condition:

Codex can create, load, update, export landscape state.

## Phase 3 — Plasticity Operators

Goal:

Implement eight core operators.

Deliverables:

```text
operator module
unit tests
operator examples
```

Exit condition:

Each operator modifies state predictably and records trace.

## Phase 4 — Query Pipeline

Goal:

Process query through hypotheses, landscape, scoring, collapse, answer planning.

Deliverables:

```text
query pipeline
hypothesis trace
collapse trace
answer prompt composer
```

Exit condition:

Given the same query, before/after plasticity state changes the selected path.

## Phase 5 — 2nd Brain Integration

Goal:

Use user’s 2nd brain safely as evidence and knowledge-transfer substrate.

Deliverables:

```text
inventory scan
sanitized summary
note templates
draft write-back folder
source index
```

Exit condition:

No existing notes are modified; draft notes are created in approved location.

## Phase 6 — Experiments and Evaluation

Goal:

Show LPSF improves over static RAG on response-tendency change.

Deliverables:

```text
experiment suite
baseline outputs
LPSF outputs
scored eval report
failure analysis
```

Exit condition:

At least three experiments show measurable before/after behavior or document why they failed.

## Phase 7 — Research Loop

Goal:

Read papers and convert them into operators, tests, or architecture changes.

Deliverables:

```text
research notes
operator extraction
source-quality log
updated LPSF spec
```

Exit condition:

Each source contributes either a concrete operator, eval criterion, architecture decision, or rejection reason.

