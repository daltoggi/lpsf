# LPSF Personalization Demo

_Generated 2026-05-28T12:35:31Z_  
_Demo corpus, MockLLM, $0 — fully reproducible via `python3 scripts/personalization_demo.py`._

This is the honest realization of the original LPSF vision: a system
whose response landscape changes after experience. Here, *experience*
= the user's picks, and *landscape change* = a persistent reranking
prior. No LLM internals are modified; the mechanism is an auditable
additive attractor over retrieval candidates.

## Step 1 — initial search (no history)

```
 #  id                           amp    rag   attr picks
------------------------------------------------------------
 1  04_local_first             0.530  0.530  0.000     0
 2  01_sqlite_for_apps         0.456  0.456  0.000     0
 3  03_fts5_search             0.000  0.000  0.000     0
```

## Step 2 — user picks `01_sqlite_for_apps` 3× (each deepens its attractor)

```
(attractor depth on path:01_sqlite_for_apps accumulates by pick_strength per pick)
```

## Step 3 — same search, now personalized

```
 #  id                           amp    rag   attr picks
------------------------------------------------------------
 1  01_sqlite_for_apps         1.356  0.456  0.900     3
 2  04_local_first             0.530  0.530  0.000     0
 3  03_fts5_search             0.000  0.000  0.000     0
```

## Step 4 — fresh process over the same on-disk state (persistence)

```
 #  id                           amp    rag   attr picks
------------------------------------------------------------
 1  01_sqlite_for_apps         1.356  0.456  0.900     3
 2  04_local_first             0.530  0.530  0.000     0
 3  03_fts5_search             0.000  0.000  0.000     0
```

## What to notice

- Initially `04_local_first` outranks `01_sqlite_for_apps` on BM25 alone.
- After 3 picks, `01_sqlite_for_apps`'s accumulated attractor depth lifts it to #1.
- The ranking change survives a process restart — it's on disk.
- Every pick is an `experience_event` row; every nudge is a `plasticity_mark` row; the boost is `rag_score + attractor_depth`. Nothing is hidden.

Try it live:

```bash
python3 scripts/lpsf_search.py search "local data storage"
python3 scripts/lpsf_search.py pick 01_sqlite_for_apps -q "local data storage"
python3 scripts/lpsf_search.py search "local data storage"   # sqlite now #1
python3 scripts/lpsf_search.py why "local data storage"       # see the math
```