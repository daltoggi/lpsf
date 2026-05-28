# LPSF on a Real Markdown FTS Corpus

_Generated 2026-05-26T12:10:40Z_

## Setup

- **Model:** claude-haiku-4-5
- **Corpus:** `data/corpus/*.md` (6 markdown notes on databases, search, RAG)
- **Index:** SQLite FTS5 at `data/corpus.fts.db` (built by `scripts/build_corpus.py`)
- **Adapter:** `LocalFTSRag` — read-only, bodies never returned
- **Baselines:** `LLMPlusRAG`, `LLMPlusLPSF`, `LLMPlusLPSFRerank` (α=β=γ=1.0)
- **User prior:** when present, `deepen_attractor(path:<target>, strength=0.5)`
- **Wall time:** 74.0s

## Results

### local_storage — `how should i store local data on a single device`

_user_prior_target: `path:01_sqlite_for_apps`, has_prior: **False**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `04_local_first` | `04_local_first`=0.752, `01_sqlite_for_apps`=0.738, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.0 |
| LLMPlusLPSF | `04_local_first` | `04_local_first`=0.752, `01_sqlite_for_apps`=0.738, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.0 |
| LLMPlusLPSFRerank | `01_sqlite_for_apps` | `04_local_first`=1.552, `01_sqlite_for_apps`=1.738, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.6 |

- LPSF flipped RAG: **False** (04_local_first → 04_local_first)
- Rerank changed LPSF: **True** (04_local_first → 01_sqlite_for_apps)

### local_storage — `how should i store local data on a single device`

_user_prior_target: `path:01_sqlite_for_apps`, has_prior: **True**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `04_local_first` | `04_local_first`=0.752, `01_sqlite_for_apps`=0.738, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.0 |
| LLMPlusLPSF | `01_sqlite_for_apps` | `04_local_first`=0.752, `01_sqlite_for_apps`=1.238, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.0 |
| LLMPlusLPSFRerank | `01_sqlite_for_apps` | `04_local_first`=1.552, `01_sqlite_for_apps`=2.238, `06_rag_evaluation`=0.0, `05_reranking`=0.0, `03_fts5_search`=0.6 |

- LPSF flipped RAG: **True** (04_local_first → 01_sqlite_for_apps)
- Rerank changed LPSF: **False** (01_sqlite_for_apps → 01_sqlite_for_apps)

### search_infra — `best way to do full-text search inside an app`

_user_prior_target: `path:03_fts5_search`, has_prior: **False**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `03_fts5_search` | `03_fts5_search`=0.569, `04_local_first`=0.0, `01_sqlite_for_apps`=0.0, `06_rag_evaluation`=0.0, `02_postgres_for_services`=0.0 |
| LLMPlusLPSF | `03_fts5_search` | `03_fts5_search`=0.569, `04_local_first`=0.0, `01_sqlite_for_apps`=0.0, `06_rag_evaluation`=0.0, `02_postgres_for_services`=0.0 |
| LLMPlusLPSFRerank | `03_fts5_search` | `03_fts5_search`=1.569, `04_local_first`=0.0, `01_sqlite_for_apps`=0.8, `06_rag_evaluation`=0.2, `02_postgres_for_services`=0.4 |

- LPSF flipped RAG: **False** (03_fts5_search → 03_fts5_search)
- Rerank changed LPSF: **False** (03_fts5_search → 03_fts5_search)

### search_infra — `best way to do full-text search inside an app`

_user_prior_target: `path:03_fts5_search`, has_prior: **True**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `03_fts5_search` | `03_fts5_search`=0.569, `04_local_first`=0.0, `01_sqlite_for_apps`=0.0, `06_rag_evaluation`=0.0, `02_postgres_for_services`=0.0 |
| LLMPlusLPSF | `03_fts5_search` | `03_fts5_search`=1.069, `04_local_first`=0.0, `01_sqlite_for_apps`=0.0, `06_rag_evaluation`=0.0, `02_postgres_for_services`=0.0 |
| LLMPlusLPSFRerank | `03_fts5_search` | `03_fts5_search`=2.069, `04_local_first`=0.0, `01_sqlite_for_apps`=0.8, `06_rag_evaluation`=0.2, `02_postgres_for_services`=0.4 |

- LPSF flipped RAG: **False** (03_fts5_search → 03_fts5_search)
- Rerank changed LPSF: **False** (03_fts5_search → 03_fts5_search)

### rag_eval — `how do i evaluate retrieval augmented generation`

_user_prior_target: `path:05_reranking`, has_prior: **False**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `06_rag_evaluation` | `06_rag_evaluation`=0.857, `05_reranking`=0.612 |
| LLMPlusLPSF | `06_rag_evaluation` | `06_rag_evaluation`=0.857, `05_reranking`=0.612 |
| LLMPlusLPSFRerank | `06_rag_evaluation` | `06_rag_evaluation`=1.857, `05_reranking`=0.612 |

- LPSF flipped RAG: **False** (06_rag_evaluation → 06_rag_evaluation)
- Rerank changed LPSF: **False** (06_rag_evaluation → 06_rag_evaluation)

### rag_eval — `how do i evaluate retrieval augmented generation`

_user_prior_target: `path:05_reranking`, has_prior: **True**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `06_rag_evaluation` | `06_rag_evaluation`=0.857, `05_reranking`=0.612 |
| LLMPlusLPSF | `05_reranking` | `06_rag_evaluation`=0.857, `05_reranking`=1.112 |
| LLMPlusLPSFRerank | `06_rag_evaluation` | `06_rag_evaluation`=1.857, `05_reranking`=1.112 |

- LPSF flipped RAG: **True** (06_rag_evaluation → 05_reranking)
- Rerank changed LPSF: **True** (05_reranking → 06_rag_evaluation)

### ranking — `ranking candidate documents for a query`

_user_prior_target: `path:05_reranking`, has_prior: **False**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `05_reranking` | `05_reranking`=0.73, `03_fts5_search`=0.45, `04_local_first`=0.372, `06_rag_evaluation`=0.361, `02_postgres_for_services`=0.0 |
| LLMPlusLPSF | `05_reranking` | `05_reranking`=0.73, `03_fts5_search`=0.45, `04_local_first`=0.372, `06_rag_evaluation`=0.361, `02_postgres_for_services`=0.0 |
| LLMPlusLPSFRerank | `05_reranking` | `05_reranking`=1.73, `03_fts5_search`=1.25, `04_local_first`=0.972, `06_rag_evaluation`=0.761, `02_postgres_for_services`=0.2 |

- LPSF flipped RAG: **False** (05_reranking → 05_reranking)
- Rerank changed LPSF: **False** (05_reranking → 05_reranking)

### ranking — `ranking candidate documents for a query`

_user_prior_target: `path:05_reranking`, has_prior: **True**_

| Baseline | Selected | Top amplitudes |
|---|---|---|
| LLMPlusRAG | `05_reranking` | `05_reranking`=0.73, `03_fts5_search`=0.45, `04_local_first`=0.372, `06_rag_evaluation`=0.361, `02_postgres_for_services`=0.0 |
| LLMPlusLPSF | `05_reranking` | `05_reranking`=1.23, `03_fts5_search`=0.45, `04_local_first`=0.372, `06_rag_evaluation`=0.361, `02_postgres_for_services`=0.0 |
| LLMPlusLPSFRerank | `05_reranking` | `05_reranking`=2.23, `03_fts5_search`=1.25, `04_local_first`=0.972, `06_rag_evaluation`=0.761, `02_postgres_for_services`=0.2 |

- LPSF flipped RAG: **False** (05_reranking → 05_reranking)
- Rerank changed LPSF: **False** (05_reranking → 05_reranking)

## Reading the table

- **`LLMPlusRAG` selected** is the pure-BM25 winner per query.
- **`LLMPlusLPSF` selected** is what changes when a user_prior attractor
  competes with BM25. A flip means LPSF's persistent prior is strong enough
  to override the raw retrieval ranking on this real corpus.
- **`LLMPlusLPSFRerank` selected** brings the LLM judge into the loop;
  a difference from LPSF means the LLM judge is correcting (or distorting)
  the LPSF choice.

Cases where all three pick the same document are uninteresting — the corpus
is unambiguous for that query. Cases where they diverge are where LPSF's
contribution is most visible.

## Compared to the synthetic experiments

Earlier experiments (H6, frontier, H7) used hand-crafted RAG fixtures with
exact scores. This run uses real BM25 over real markdown — the score margins
are determined by the corpus statistics, not by us. The same selection
equation `c* = argmax(α·r + β·ℓ + γ·a)` applies; only the inputs are now
from the actual retrieval engine.