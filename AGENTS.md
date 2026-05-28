# AGENTS.md — LPSF Project Agent Rules

이 파일은 Codex와 기타 coding agent가 이 repo에서 작업할 때 항상 따라야 할 운영 규칙입니다.

## Mission

Build **LPSF-v0.1: Landscape-Plastic Semantic Field**, a prototype where experience changes future response tendencies through an external, inspectable landscape state rather than merely rereading stored text.

The first milestone is not a new foundation model. It is a working prototype that proves:

1. Experience events can be encoded.
2. Plasticity operators can modify a persistent landscape state.
3. Similar inputs before/after experience produce meaningfully different response paths.
4. The change is explainable through stored marks, attractors, opened/inhibited paths, and value/sensitivity shifts.
5. The system can read from the user's 2nd brain safely and write back only curated notes or drafts.

## Core Theory Constraints

Use this framing:

```text
Memory is not recall.
Memory is landscape deformation.
```

Do not reduce the project to ordinary RAG. RAG is allowed as an evidence layer, but LPSF must additionally maintain persistent state that changes future retrieval, ranking, hypothesis formation, and answer planning.

## Non-Negotiable Safety Rules

- Do not delete, move, rewrite, or reorganize existing 2nd brain notes unless explicitly authorized.
- Do not commit raw private 2nd brain content to public repos.
- Do not export sensitive personal notes into prompts, logs, screenshots, issues, or remote services unless the user explicitly authorizes that scope.
- Do not write secrets, tokens, API keys, or `.env` values into markdown, tests, logs, or commits.
- Do not use production DBs, live customer data, or external deployment targets.
- Do not claim an idea is experimentally proven unless there is an implemented eval result.
- Do not present quantum, biological epigenetic, or gravity language as literal physics/biology unless the implementation supports it. Use operational definitions.

## Approved Write Locations

By default, write project-generated files only to:

```text
docs/lpsf/
research/lpsf/
experiments/lpsf/
ops/lpsf/
second_brain_drafts/lpsf/
```

For 2nd brain writes, use an append-only draft folder such as:

```text
<SECOND_BRAIN_DIR>/00_Inbox/LPSF/Codex-Drafts/
```

If that folder does not exist, propose creation and create it only after confirmation or if the user has already authorized 2nd brain write access.

## Required First Actions

Before implementation, inspect and summarize:

1. Repo structure.
2. Existing `AGENTS.md`, `README`, `pyproject`, package files, test commands.
3. Existing data, notebooks, experiments, docs.
4. 2nd brain path and access status.
5. Whether there is any existing RAG/vector DB/Obsidian integration.
6. Current build/test/lint commands.

Write the findings to:

```text
ops/lpsf/PROJECT_CONTEXT.md
```

## Done Definition for LPSF-v0.1

A v0.1 run is done only when all of these exist:

1. Project context report.
2. 2nd brain inventory summary or access-blocked note.
3. Minimal persistent landscape state model.
4. Implemented plasticity operator stubs or working functions.
5. At least three before/after experiments.
6. Baseline comparison against ordinary RAG or static memory.
7. Evaluation report with failures and next steps.
8. Status log updated.
9. No unsafe raw private data committed.

## Preferred Agent Loop

Use this loop:

```text
Plan → inspect → implement smallest slice → run tests/evals → observe → repair → document → repeat
```

Keep a compact status log after each checkpoint:

```text
Checkpoint:
Changed:
Verified:
Failed:
Next:
Blocked:
Risk:
```

## Development Conventions

- Prefer small, inspectable modules over monolithic agent code.
- Prefer deterministic tests for plasticity operators.
- For LLM-dependent tests, record prompts, outputs, and evaluator notes separately.
- Make the landscape state inspectable as JSON/SQLite tables before neuralizing it.
- Keep all data schemas explicit.
- Keep raw traces, semantic summaries, and plasticity marks separate.

## Terminology Rules

Use these implementation names:

- `landscape_state`: persistent response-tendency state.
- `experience_event`: an event that may update the landscape.
- `plasticity_mark`: stored change to node, edge, path, value, schema, or sensitivity.
- `attractor`: response path that becomes easier to activate.
- `hypothesis_state`: one candidate interpretation held before collapse.
- `interference_matrix`: support/inhibition relation among hypotheses.
- `collapse_trace`: record of why a final response path was selected.
- `second_brain`: user's personal knowledge base.

## Avoid

- No vague “AI consciousness” claims.
- No “just add memory” implementation.
- No giant architecture before operator tests.
- No autonomous web scraping without source-quality rules.
- No unbounded goal without stopping condition.

