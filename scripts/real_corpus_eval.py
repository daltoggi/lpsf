#!/usr/bin/env python3
"""Real-corpus evaluation: LPSF on a small but real markdown FTS index.

For each of several queries, runs three baselines:
  - LLMPlusRAG         (BM25 only)
  - LLMPlusLPSF        (BM25 + attractor)
  - LLMPlusLPSFRerank  (BM25 + LLM judge + attractor)

with two attractor configurations:
  - "no_prior":   no deepen_attractor calls before the query
  - "user_prior": deepen path:<user_preferred_doc> with strength 0.5

We log: BM25 top-3, selected_path per baseline per condition, and whether
LPSF flipped the BM25 winner. The user_prior simulates "the user has
historically engaged more with document X" — a realistic personalization
setup.

Cost estimate: ~$0.05 with haiku.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

CORPUS_DB = REPO_ROOT / "data" / "corpus.fts.db"
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "REAL_CORPUS_EVAL.md"

# Each scenario picks a query + a "user prior" document to deepen on.
# Choices reflect plausible personalization: a user who keeps clicking
# `01_sqlite_for_apps` should see SQLite results promoted on related queries.
SCENARIOS = [
    {
        "name": "local_storage",
        "query": "how should i store local data on a single device",
        "user_prior_target": "01_sqlite_for_apps",
    },
    {
        "name": "search_infra",
        "query": "best way to do full-text search inside an app",
        "user_prior_target": "03_fts5_search",
    },
    {
        "name": "rag_eval",
        "query": "how do i evaluate retrieval augmented generation",
        "user_prior_target": "05_reranking",
    },
    {
        "name": "ranking",
        "query": "ranking candidate documents for a query",
        "user_prior_target": "05_reranking",
    },
]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if not os.environ.get(k.strip()):
            os.environ[k.strip()] = v.strip()


def run_scenario(model: str, scenario: dict, has_prior: bool, seed: int):
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusLPSF, LLMPlusLPSFRerank, LLMPlusRAG
    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.local_fts_rag import LocalFTSRag
    from lpsf.experiments.prompts import PAIRWISE_JUDGE_PROMPT
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )
    from lpsf.operators.deepen_attractor import deepen_attractor

    snap = f"snap_corpus_{scenario['name']}_{has_prior}_{seed}"
    evt = f"evt_corpus_{scenario['name']}_{has_prior}_{seed}"
    conn = db.init_db(":memory:")
    insert_synthetic_snapshot(conn, snapshot_id=snap)
    insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)
    if has_prior:
        target = f"path:{scenario['user_prior_target']}"
        deepen_attractor(
            conn,
            event_id=evt,
            snapshot_id=snap,
            target_type="path",
            target_id=target,
            strength=0.5,
            half_life=3600,
            evidence_refs=[scenario["user_prior_target"]],
            reason=f"user_prior on {scenario['user_prior_target']}",
            scope="real_corpus_eval",
        )

    rag = LocalFTSRag(db_path=str(CORPUS_DB), snapshot_id=snap)
    main_llm = ClaudeLLM(model=model, temperature=0.0)
    judge_llm = ClaudeLLM(
        model=model,
        temperature=0.0,
        system_prompt=PAIRWISE_JUDGE_PROMPT,
        cache_dir=os.path.expanduser("~/.cache/lpsf/claude_judge"),
    )

    plain_rag = LLMPlusRAG()
    lpsf = LLMPlusLPSF()
    rerank = LLMPlusLPSFRerank(alpha=1.0, beta=1.0, gamma=1.0, judge_llm=judge_llm)

    out = {
        "scenario": scenario["name"],
        "query": scenario["query"],
        "user_prior_target": scenario["user_prior_target"],
        "has_prior": has_prior,
    }
    try:
        r1 = plain_rag.respond(conn, query=scenario["query"], snapshot_id=snap, llm=main_llm, rag=rag, seed=seed)
        out["LLMPlusRAG"] = {
            "selected": r1.selected_path,
            "candidates": r1.candidates[:5],
            "amplitudes": {k: round(v, 3) for k, v in list(r1.amplitudes.items())[:5]},
        }
        r2 = lpsf.respond(conn, query=scenario["query"], snapshot_id=snap, llm=main_llm, rag=rag, seed=seed)
        out["LLMPlusLPSF"] = {
            "selected": r2.selected_path,
            "amplitudes": {k: round(v, 3) for k, v in list(r2.amplitudes.items())[:5]},
        }
        r3 = rerank.respond(conn, query=scenario["query"], snapshot_id=snap, llm=main_llm, rag=rag, seed=seed)
        out["LLMPlusLPSFRerank"] = {
            "selected": r3.selected_path,
            "amplitudes": {k: round(v, 3) for k, v in list(r3.amplitudes.items())[:5]},
        }
    finally:
        rag.close()
        conn.close()

    main_cost = float(getattr(getattr(main_llm, "usage", None), "cost", lambda: 0.0)())
    judge_cost = float(getattr(getattr(judge_llm, "usage", None), "cost", lambda: 0.0)())
    out["cost"] = main_cost + judge_cost
    return out


def render_report(rows: List[Dict[str, Any]], model: str, elapsed: float) -> None:
    lines = [
        "# LPSF on a Real Markdown FTS Corpus",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        "- **Corpus:** `data/corpus/*.md` (6 markdown notes on databases, search, RAG)",
        "- **Index:** SQLite FTS5 at `data/corpus.fts.db` (built by `scripts/build_corpus.py`)",
        "- **Adapter:** `LocalFTSRag` — read-only, bodies never returned",
        "- **Baselines:** `LLMPlusRAG`, `LLMPlusLPSF`, `LLMPlusLPSFRerank` (α=β=γ=1.0)",
        "- **User prior:** when present, `deepen_attractor(path:<target>, strength=0.5)`",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
    ]
    for row in rows:
        title = f"### {row['scenario']} — `{row['query']}`"
        lines.append(title)
        lines.append("")
        lines.append(f"_user_prior_target: `path:{row['user_prior_target']}`, "
                     f"has_prior: **{row['has_prior']}**_")
        lines.append("")
        lines.append("| Baseline | Selected | Top amplitudes |")
        lines.append("|---|---|---|")
        for bn in ("LLMPlusRAG", "LLMPlusLPSF", "LLMPlusLPSFRerank"):
            entry = row[bn]
            amps_str = ", ".join(f"`{k.split(':')[-1]}`={v}" for k, v in entry["amplitudes"].items())
            lines.append(f"| {bn} | `{entry['selected'].split(':')[-1]}` | {amps_str} |")
        # Did LPSF flip?
        rag_pick = row["LLMPlusRAG"]["selected"]
        lpsf_pick = row["LLMPlusLPSF"]["selected"]
        rerank_pick = row["LLMPlusLPSFRerank"]["selected"]
        flipped_by_lpsf = rag_pick != lpsf_pick
        rescued_by_rerank = lpsf_pick != rerank_pick
        lines.append("")
        lines.append(
            f"- LPSF flipped RAG: **{flipped_by_lpsf}** "
            f"({rag_pick.split(':')[-1]} → {lpsf_pick.split(':')[-1]})"
        )
        lines.append(
            f"- Rerank changed LPSF: **{rescued_by_rerank}** "
            f"({lpsf_pick.split(':')[-1]} → {rerank_pick.split(':')[-1]})"
        )
        lines.append("")
    lines += [
        "## Reading the table",
        "",
        "- **`LLMPlusRAG` selected** is the pure-BM25 winner per query.",
        "- **`LLMPlusLPSF` selected** is what changes when a user_prior attractor",
        "  competes with BM25. A flip means LPSF's persistent prior is strong enough",
        "  to override the raw retrieval ranking on this real corpus.",
        "- **`LLMPlusLPSFRerank` selected** brings the LLM judge into the loop;",
        "  a difference from LPSF means the LLM judge is correcting (or distorting)",
        "  the LPSF choice.",
        "",
        "Cases where all three pick the same document are uninteresting — the corpus",
        "is unambiguous for that query. Cases where they diverge are where LPSF's",
        "contribution is most visible.",
        "",
        "## Compared to the synthetic experiments",
        "",
        "Earlier experiments (H6, frontier, H7) used hand-crafted RAG fixtures with",
        "exact scores. This run uses real BM25 over real markdown — the score margins",
        "are determined by the corpus statistics, not by us. The same selection",
        "equation `c* = argmax(α·r + β·ℓ + γ·a)` applies; only the inputs are now",
        "from the actual retrieval engine.",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env.local")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    from lpsf.experiments.cost import PRICING
    rates = PRICING.get(args.model, {"input": 0, "output": 0})
    cells = len(SCENARIOS) * 2  # has_prior=False then True
    # Per cell: 1 main LLM call + up to k*(k-1)/2 judge calls (k candidates)
    # Assume avg k=4 → 6 judge calls + 1 main = 7 calls/cell
    total_calls = cells * 7
    print(f"Model: {args.model}")
    print(f"Scenarios: {len(SCENARIOS)} × 2 prior conditions = {cells} cells")
    print(f"Estimated LLM calls: ~{total_calls}")
    print(f"Estimated cost: ~${total_calls * 80 * rates['output'] / 1_000_000:.4f}")
    if args.dry_run:
        print("=== DRY RUN ===")
        return

    print()
    rows = []
    total_cost = 0.0
    started = time.time()
    for sc in SCENARIOS:
        for has_prior in (False, True):
            t0 = time.time()
            print(f"{sc['name']:>15} prior={has_prior} ...", end=" ", flush=True)
            out = run_scenario(args.model, sc, has_prior=has_prior, seed=0)
            rows.append(out)
            total_cost += out["cost"]
            print(
                f"RAG={out['LLMPlusRAG']['selected'].split(':')[-1]} "
                f"LPSF={out['LLMPlusLPSF']['selected'].split(':')[-1]} "
                f"RR={out['LLMPlusLPSFRerank']['selected'].split(':')[-1]} "
                f"({time.time()-t0:.1f}s)"
            )
    elapsed = time.time() - started
    render_report(rows, args.model, elapsed)
    print(f"\nTotal cost: ${total_cost:.4f} | Wall: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
