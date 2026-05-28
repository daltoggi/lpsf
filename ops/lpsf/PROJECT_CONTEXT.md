# LPSF M0 Project Context

Date: 2026-05-23
Scope: M0 Context Capture only. No code, schema, operators, package installs, or M1-M5 work performed.

## Access Mode

- Repo root: `~/lpsf`.
- 2nd brain root from `.env.local`: `~/second-brain`.
- LPSF lab from `.env.local`: `~/second-brain/project-labs/lpsf`.
- `SECOND_BRAIN_MODE=2`, interpreted as lab-write mode with `brain-core` read-only.
- Privacy boundary: repo outputs are sanitized/public-level; lab outputs may hold fuller local detail, but lab writes were blocked by the current filesystem sandbox. See `ops/lpsf/STATUS_LOG.md`.

## Repo Structure Summary

This repo is currently a markdown planning pack, not an implementation repo.

```text
.
├── README.md
├── AGENTS.md
├── PLANS.md
├── MANIFEST.md
├── codex/
├── docs/
├── experiments/
├── ops/
├── prompts/
├── research/
├── second_brain/
└── templates/
```

Observed file groups:

- `docs/`: LPSF thesis, architecture, operators, memory/forgetting, schema draft, roadmap, risk register, references, and v0.1 spec.
- `experiments/`: experiment plan and eval/benchmark markdown only.
- `second_brain/`: safe protocol, scan plan, and note templates.
- `research/`: research queue, paper reading protocol, source quality rules.
- `ops/`: safe workflow and status log template.
- `codex/`, `prompts/`, `templates/`: runbooks, goal prompts, review prompts, and report templates.

No `src/`, `tests/`, `data/`, `notebooks/`, `.data/`, package manifest, or executable implementation files were found in the repo.

## Required Files Read

Read completely before scanning:

- `README.md`
- `AGENTS.md`
- `PLANS.md`
- `docs/01_LPSF_THESIS.md`
- `docs/02_ARCHITECTURE.md`
- `second_brain/2ND_BRAIN_PROTOCOL.md`
- `second_brain/2ND_BRAIN_SCAN_PLAN.md`
- `ops/SAFE_WORKFLOW.md`
- `.env.local`
- `~/second-brain/AGENTS.md`
- `~/second-brain/brain-core/AGENTS.md`
- `~/second-brain/project-labs/AGENTS.md`
- `~/second-brain/project-labs/lpsf/AGENTS.md`

Additional governance/context read:

- `ops/STATUS_LOG_TEMPLATE.md`
- `MANIFEST.md`
- `.gitignore`
- `~/second-brain/catalog-engine/CHAT_PROTOCOL.md`
- `~/second-brain/project-labs/lpsf/README.md`

## Build, Test, Lint Commands

Detected package/config files: none.

No current build/test/lint commands are defined in this repo. Specifically, no `pyproject.toml`, `package.json`, `requirements*.txt`, `Makefile`, `justfile`, `pytest.ini`, `ruff.toml`, `tox.ini`, `setup.py`, or `setup.cfg` was found within depth 3.

Available local tooling observed:

- Python: `Python 3.9.6`
- Node: `v25.8.0`
- SQLite CLI: `3.51.0`
- ripgrep: `15.1.0`

Implication for M1/M2: implementation dependencies are not declared yet. Before code work, the user should choose a packaging/runtime boundary, likely Python + SQLite if staying closest to the current 2nd brain infrastructure.

## Current Code Patterns

There is no application code yet. Existing patterns are documentation-first:

- Markdown specs and runbooks.
- Explicit safety boundaries.
- Status-log checkpoint format.
- Operational terminology from `AGENTS.md`: `landscape_state`, `experience_event`, `plasticity_mark`, `attractor`, `hypothesis_state`, `interference_matrix`, `collapse_trace`, `second_brain`.

## 2nd Brain Top-Level Structure

From the root 2nd brain constitution, sanitized to zone names and roles only:

| Zone | Role | Codex write posture |
|---|---|---|
| `brain-core/` | Canon / Obsidian vault | Restricted; canon zones are read-only except approved automation path |
| `brain-source/` | Raw and normalized sources | Sidecars/registry workflow only |
| `project-labs/` | Experiment labs | Free within lab rules |
| `brain-backroom/` | Machine cache/logs | Free for machine artifacts |
| `import-board/` | Promotion review board | Inbox drafts only |
| `catalog-engine/` | Search/router/manifests | Scripts and tooling area |
| `docs-system/` | Design/contracts | No writes |
| `_thinking_os/` | Reasoning/evals/RAG/policy workspace | Free within zone; no `brain-core` writes |

Hard write prohibitions in effect:

- No writes under `brain-core/01_concepts/`, `02_decisions/`, `03_workflows/`, `04_assets/`, `05_works/`, or `07_projects/`.
- No writes under `docs-system/`.
- No processing/export of notes with `sensitivity: high` or `external_llm: false`.
- No raw private brain content in repo outputs.

## 2nd Brain Inventory Snapshot

Metadata scan only for repo-public context:

- `brain-core` markdown total: 143 files.
- `brain-core` hard-sensitive markdown notes detected by frontmatter: 0.
- Content-scanned non-sensitive `brain-core` markdown notes: 143.
- Major `brain-core` zone counts:
  - `00_inbox`: 4
  - `01_concepts`: 36
  - `02_decisions`: 2
  - `03_workflows`: 15
  - `04_assets`: 44
  - `06_reviews`: 20
  - `_archive`: 19
  - root/support markdown: 3
- Dominant non-sensitive frontmatter `type` distribution:
  - `asset`: 46
  - `concept`: 40
  - missing type: 18
  - `workflow`: 16
  - `synthesis`: 12
  - `portal`: 9
  - `decision`: 2

The source registry has a stricter boundary:

- `brain-source/registry.jsonl`: 141 parsed source records.
- Source registry sensitivity flags:
  - normal: 134
  - high or external-blocked: 7
- Source contents for high/external-blocked records were not read or processed.

## Existing RAG / Vector / Obsidian Infrastructure

Discovered local infrastructure:

- `brain-backroom/fts.db` exists.
  - Tables: `notes`, `embeddings`, `index_meta`, `notes_fts`, and FTS support tables.
  - Count-only query: `notes=382`, `embeddings=382`, `index_meta=6`.
- `brain-backroom/cache/fastembed/` exists and contains local FastEmbed model cache directories.
- `brain-backroom/embeddings/` exists but currently has 0 files.
- `brain-source/registry.jsonl` exists with 141 parsed records.
- `brain-source/sources/` has 143 source directories and 1,938 files.
- `_thinking_os/rag/` exists with 8 markdown files.
- `_thinking_os/evals/` exists with 16 files.
- `_thinking_os/reasoning/` exists with 10 markdown files.
- `catalog-engine/` exists with:
  - router Python modules
  - FTS/retrieval scripts
  - registry/source graph scripts
  - router tests
  - one manifest CSV
- `catalog_engine.router --chat-doctor` reported OK and confirmed retrieval index availability:
  - indexed: 382
  - zones: core 119, inbox 27, lab 45, source 160, system 4, thinking_os 27
  - embedding provider: FastEmbed multilingual MiniLM, dim 384

## LPSF-Relevant Brain Clusters

High-level clusters only; no private note titles are included.

Lexical signal counts from non-sensitive `brain-core` content:

- Economy/market reasoning: 1,036 hits.
- Cognition/memory/psychology: 380 hits.
- Agent/Codex/workflow: 372 hits.
- Decision/plasticity-like rules: 366 hits.
- Knowledge management / 2nd brain / canon promotion: 302 hits.
- Automation/router/pipeline: 183 hits.
- RAG/memory/retrieval/vector/embedding: 155 hits.
- Thinking OS / reasoning / counterpoint: 151 hits.

Potential LPSF substrate clusters:

- Evidence layer: `brain-source`, source registry, normalized source packs, `brain-core` canon notes, `_thinking_os` RAG/eval artifacts.
- Semantic layer: `brain-core/01_concepts`, concept-domain taxonomy, `06_reviews`, source-backed synthesis notes, catalog-engine retrieval metadata.
- Landscape layer: `02_decisions` as durable preference/constraint marks, `03_workflows` as opened/inhibited paths, lab `lessons/` as future inhibit-path inputs, router/chat protocol as current collapse-routing policy.

Likely attractor candidates:

- Safe canon promotion and source-grounded knowledge management.
- Context engineering, verification loops, and agent workflow discipline.
- RAG/retrieval as evidence, not authority.
- Reasoning/evaluation/contra-case workflow from `_thinking_os`.
- Finance/market reasoning as a dense domain substrate for later controlled experiments, if the user permits it.

## Existing Data, Notebooks, Experiments, Docs

Repo-local:

- Docs: extensive markdown specification pack exists.
- Experiments: markdown plans exist, but no executable experiment harness.
- Data/notebooks: none found.
- Code/tests: none found.

Brain-local:

- Search/index data exists in `brain-backroom/fts.db`.
- Source registry and normalized source directories exist.
- `_thinking_os` has reasoning, eval, RAG, policy, audit, and report material.
- `import-board` has active promotion workflow state:
  - inbox: 45 files
  - ready: 5 files
  - accepted: 91 files
  - flagged: 0 files
  - archive: 76 files

## Missing Dependencies / Decisions Before Implementation

No dependencies are declared in this repo. Before M2 implementation, decide:

- Python package layout and dependency manager, or explicitly keep M1 docs-only.
- SQLite schema ownership: reuse/read existing `brain-backroom/fts.db` vs create isolated LPSF state DB.
- Whether embeddings should be reused from the existing FastEmbed index or treated only as external evidence.
- Test runner and minimum deterministic test command.
- Privacy policy for which brain zones can be used as eval substrate.

## Open Questions Before M1

1. Should M1 treat existing `brain-backroom/fts.db` as read-only evidence infrastructure, or should LPSF create a separate isolated `landscape_state` store?
2. Which brain domains are approved for later before/after experiments: knowledge-management/AI only, or also economy/market/self-operation clusters?
3. Should repo-public docs continue avoiding brain note titles entirely, while lab-local drafts may include note titles?
4. For source registry records marked high/external-blocked, should LPSF exclude them entirely or allow count-only metadata for local diagnostics?
5. Preferred implementation language for M2: Python + SQLite, Node, or docs-only schema first?
6. Should M1 normalize theory strictly from the pack, or may it incorporate high-level substrate-fit observations from this M0 scan?

## M0 Boundary

M0 context capture was performed up to the point allowed by the active sandbox. Repo deliverable 1 was written here. Lab-local deliverables could not be written because the active writable roots do not include `~/second-brain`.
