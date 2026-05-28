# Subagent Orchestration Plan

Codex may split work into parallel threads or subagent-like responsibilities. Each role has file ownership and input/output constraints.

## 1. Repo Scout

Input:

- repo files;
- package manifests;
- README;
- tests;
- existing `AGENTS.md`.

Output:

```text
ops/lpsf/PROJECT_CONTEXT.md
```

File ownership:

- read all repo files as needed;
- write only ops/lpsf context/status files.

## 2. 2nd Brain Curator

Input:

- `SECOND_BRAIN_DIR` if configured;
- 2nd brain protocol.

Output:

```text
second_brain_drafts/lpsf/2ND_BRAIN_INVENTORY_SUMMARY.md
<SECOND_BRAIN_DIR>/00_Inbox/LPSF/Codex-Drafts/*.md if authorized
```

File ownership:

- read-only for existing notes;
- draft-only writes.

## 3. Research Scout

Input:

- research queue;
- existing source notes;
- official docs and papers if web/browser is available.

Output:

```text
research/lpsf/*.md
```

Rules:

- record source metadata;
- separate claim/evidence/speculation;
- do not hallucinate citations;
- extract operators, not just summaries.

## 4. Architecture Designer

Input:

- LPSF thesis;
- operator spec;
- repo context.

Output:

```text
docs/lpsf/LPSF_SPEC.md
docs/lpsf/ARCHITECTURE_DECISIONS.md
```

## 5. Prototype Builder

Input:

- schema;
- architecture spec;
- repo conventions.

Output:

- storage layer;
- operator functions;
- query pipeline;
- tests.

## 6. Experiment Runner

Input:

- experiment plan;
- prototype;
- baselines.

Output:

```text
experiments/lpsf/*.md
experiments/lpsf/results/*
```

## 7. Evaluator

Input:

- experiment outputs;
- eval rubric.

Output:

```text
experiments/lpsf/EVALUATION_REPORT.md
```

## 8. Safety Auditor

Input:

- changed files;
- status log;
- 2nd brain drafts.

Output:

```text
ops/lpsf/SAFETY_REVIEW.md
```

Checks:

- no secrets;
- no raw private notes in repo;
- no unauthorized modifications;
- no unsupported claims.

