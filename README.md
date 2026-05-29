# LPSF — Landscape-Plastic Semantic Field

![tests](https://img.shields.io/badge/tests-206%20passing-brightgreen)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![cost](https://img.shields.io/badge/total%20experimental%20cost-%240.74-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![status](https://img.shields.io/badge/status-research%20v0.1-yellow)

**An honest, hands-on attempt to give an LLM real memory — and a precise map of
why it's hard.** LLMs re-read instead of remembering; this repo asks whether
experience can change the model's *state* (not just its input), measures three
substrates for doing so on a frozen 0.5B model for ~$1, and states every limit
out loud — including a wild intuition that failed for a reason worth the project.

**→ Start with the essay: [`docs/blog/lpsf_journey.md`](docs/blog/lpsf_journey.md)**
("I tried to give an LLM real memory. I failed precisely — and that was the point.")
Then the map: [`docs/lpsf/MEMORY_SUBSTRATES.md`](docs/lpsf/MEMORY_SUBSTRATES.md).

It does **not** invent new methods or modify pretraining. The activation steering
reproduces CAA; the weight-memory and forgetting reproduce known continual-learning
behavior. The value is a complete, honest, reproducible pass that places mem0 /
MemGPT / ROME / TTT / CAA on one axis (memory in the *input* vs the *state*), with
measured trade-offs and negative controls. Not SOTA, not a product — a way of
thinking, with the receipts. Honest scope: [`docs/lpsf/CURRENT_STATUS.md`](docs/lpsf/CURRENT_STATUS.md).

## Two tracks (and where they sit in the field)

The project explored both ways an LLM could "remember", and measured the trade-offs by hand:

1. **Context-management track** (frozen model, smarter retrieval) — the reranking layer
   described below. Same family as mem0 / MemGPT / LangMem. Inspectable, but it changes
   *what is selected*, not the model's *response*; it still re-reads.
2. **State-based track** (the model's own state changes) — `src/lpsf/substrate/`:
   - LoRA-from-experience: teaches a fictional fact into the **weights**; recalled with an
     empty context (0.00 → 1.00), but multiple facts collapse to last-write-wins.
   - Activation steering (a reimplementation of [CAA](https://arxiv.org/abs/2312.06681)):
     a persistent vector in the residual stream shifts responses, graded and reversible,
     with a multi-concept *coexistence window* that weights lack.

**[`docs/lpsf/MEMORY_SUBSTRATES.md`](docs/lpsf/MEMORY_SUBSTRATES.md)** places all of this —
mem0, MemGPT, ROME, [TTT](https://arxiv.org/abs/2407.04620), CAA — on **one axis** (memory
in the *input* vs the *state*), with the hands-on measurements, and the project's own lens:
a substrate-agnostic operator layer tested by one falsifiable question (does the response
change *without re-reading*, reversibly?). It is a learning + synthesis artifact, not a
SOTA claim.

---

## The mechanism, in one line

LPSF reranks RAG candidates with an accumulated prior. Two baselines:

```
LLMPlusLPSF        c* = argmax_c [ r(c) + a(c) ]
LLMPlusLPSFRerank  c* = argmax_c [ α·r(c) + β·ℓ(c) + γ·a(c) ]
```

| term | meaning |
|---|---|
| `r(c)` | first-stage retrieval (BM25 / RAG) score for candidate `c` |
| `a(c)` | accumulated **attractor depth** from past `deepen`/`weaken`/decay operators |
| `ℓ(c)` | optional LLM-as-judge pairwise score (only when `β > 0`) |
| `α,β,γ` | tunable weights: retrieval vs. LLM judgment vs. persistent prior |

A candidate `B` overrides the retrieval winner `A` exactly when
`γ·Δa > α·Δr + β·Δℓ`. That boundary is not hand-waved — it's measured (below).

---

## What's proven (six properties, each backed by tests + scripts)

| Property | Evidence | Cost |
|---|---|---:|
| **Controllability** — LPSF can override RAG rankings | H6 adversarial: 10/10 seeds, baselines diverge | $0.01 |
| **Predictability** — exact decision boundary `Δa > Δr` | rank-flip frontier: 121/121 grid cells on the diagonal | $0 |
| **Reversibility (operator)** — bias undoable by counter-experience | H7: deepen → weaken reverses → competing deepen overrides | $0 |
| **Reversibility (decay)** — bias fades over time via `half_life` | H8: 3 half-lives flips selection back | $0 |
| **Tunability** — `β` trades attractor autonomy vs. LLM-judge safety | H6 β-sweep: predicted threshold `β > 0.30` confirmed exactly | $0.002 |
| **Personalization** — real picks reshape future rankings, persisted | `lpsf-search` CLI + persistence tests | $0 |

Total experimental spend across the **entire** project: **~$0.74** (file-cached;
re-runs are free).

## What is NOT proven (please don't quote these)

- ❌ **"LPSF makes LLM reasoning plastic."** Selection is decoupled from LLM
  output text; even in the rerank baseline the LLM is just one weighted term.
- ❌ **"Generalizes to large/real corpora."** Tested on a 6-doc demo corpus and
  a single personal FTS index (plumbing only). No broad benchmark yet.
- ❌ **"Eight operators = eight learning rules."** They're update policies on a
  single `attractor_depth` field. The diversity is in *how* depth changes.
- ❌ **"Always improves correctness."** A miscalibrated prior can degrade results;
  the `β` LLM-judge channel mitigates but doesn't eliminate this.

---

## Quickstart

```bash
pip install -e ".[dev]"

# Full deterministic test suite — no API keys needed (everything paid is mocked)
python3 -m pytest -q            # 206 passing

# Build the demo FTS corpus (deterministic, gitignored)
python3 scripts/build_corpus.py
```

### Try the personalizing search CLI (no API key, $0)

```bash
python3 scripts/lpsf_search.py search "local data storage"
#   #1 04_local_first   amp=0.530 ...
#   #2 01_sqlite_for_apps amp=0.456 ...

python3 scripts/lpsf_search.py pick 01_sqlite_for_apps -q "local data storage"
python3 scripts/lpsf_search.py pick 01_sqlite_for_apps -q "local data storage"

python3 scripts/lpsf_search.py search "local data storage"
#   #1 01_sqlite_for_apps amp=1.056  ← picked   (rose above local_first)

python3 scripts/lpsf_search.py why "local data storage"
#   amplitude = rag(0.456) + attractor(0.600) = 1.056   [picked 2x]
```

The preference is written to an on-disk state DB and survives restarts. Picks
fade with a 30-day half-life. Add `--rerank` to enable the LLM-judge channel
(needs `ANTHROPIC_API_KEY`), or `--brain` to point at a sensitivity-gated
personal FTS index via `LPSF_BRAIN_FTS`.

### Reproduce the experiments

```bash
python3 scripts/rank_flip_frontier.py     # $0  — decision boundary
python3 scripts/plot_frontier.py          # $0  — Unicode heatmap
python3 scripts/run_benchmark.py --mode standard   # ~$0.26 (needs API key)
python3 scripts/h6_with_rerank.py         # ~$0.002 — β safety-net threshold
python3 scripts/regenerate_report.py      # $0  — re-render report from JSON
```

---

## Repo layout

```
data/corpus/                 6 markdown notes (read-only RAG substrate)
docs/lpsf/CURRENT_STATUS.md  canonical honest positioning  ← read this
docs/lpsf/LPSF_SPEC.md       the theoretical aspiration (direction, not code)
docs/CODEX_PACK_KO.md        original Korean operating-pack intro
LPSF_PROJECT_SUMMARY.md      one-page handoff
src/lpsf/
  db.py, schema.sql          13-table SQLite state store
  operators/                 8 update policies + decay
  experiments/
    baselines.py             the selection equations live here
    local_fts_rag.py         read-only FTS5 adapter
    brain_backroom_rag.py    sensitivity-gated personal-index adapter
    hypotheses/h1..h8.py     eight falsifiable scenarios
  app/session.py             LPSFSearchSession — persistent personalization
scripts/                     reproducible runners + the lpsf-search CLI
ops/lpsf/                    generated reports + STATUS_LOG
tests/                       206 deterministic tests
ci/github-actions-test.yml   CI workflow (see note below)
```

## Key documents

- [`LPSF_PROJECT_SUMMARY.md`](LPSF_PROJECT_SUMMARY.md) — start here (1 page)
- [`docs/lpsf/CURRENT_STATUS.md`](docs/lpsf/CURRENT_STATUS.md) — proven vs. not-proven
- [`ops/lpsf/RANK_FLIP_FRONTIER.md`](ops/lpsf/RANK_FLIP_FRONTIER.md) — the decision boundary
- [`ops/lpsf/PERSONALIZATION_DEMO.md`](ops/lpsf/PERSONALIZATION_DEMO.md) — the tool in action
- [`docs/blog/2026-05-28_lpsf_journey.md`](docs/blog/2026-05-28_lpsf_journey.md) — the build narrative

## CI

The GitHub Actions workflow is shipped at `ci/github-actions-test.yml` (kept
outside `.github/workflows/` so it pushes without the OAuth `workflow` scope).
To activate:

```bash
gh auth refresh -h github.com -s workflow
mkdir -p .github/workflows && git mv ci/github-actions-test.yml .github/workflows/test.yml
git commit -m "Activate CI" && git push
```

## License

MIT — see [`LICENSE`](LICENSE).
