#!/usr/bin/env python3
"""Smoke evaluation of LPSF against a real 2nd-brain FTS index.

SAFETY DESIGN (read before running):
  - Uses BrainBackroomRag, which opens the index read-only and excludes any
    note with sensitivity=high or external_llm=false.
  - The committed report (ops/lpsf/BRAIN_SMOKE.md) logs ONLY aggregate
    statistics and opaque note rowids. It NEVER writes note titles, paths,
    or content to disk.
  - Note summaries are sent to the LLM judge (Anthropic) for pairwise
    ranking. Per the 2nd-brain contract this is permitted only for notes
    that are NOT high-sensitivity and NOT external_llm=false — exactly the
    notes the adapter's gate allows through.
  - Queries are generic technical topics chosen to avoid personal subjects.

Usage:
    python3 scripts/brain_backroom_eval.py --dry-run        # counts only, no API
    python3 scripts/brain_backroom_eval.py                  # ~$0.05 haiku
    python3 scripts/brain_backroom_eval.py --db /path/to/fts.db
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

# No personal path is hard-coded. Point this at your own brain-backroom-style
# FTS index via --db or the LPSF_BRAIN_FTS environment variable.
DEFAULT_DB = os.environ.get("LPSF_BRAIN_FTS", "")
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "BRAIN_SMOKE.md"

# Generic technical queries; deliberately impersonal.
QUERIES = [
    "retrieval augmented generation",
    "knowledge management workflow",
    "language model evaluation",
    "vector embeddings semantic search",
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


def run_query(db_path: str, query: str, model: str) -> Dict[str, Any]:
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusLPSFRerank, LLMPlusRAG
    from lpsf.experiments.brain_backroom_rag import BrainBackroomRag
    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.prompts import PAIRWISE_JUDGE_PROMPT
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )

    conn = db.init_db(":memory:")
    snap = "snap_brain"
    insert_synthetic_snapshot(conn, snapshot_id=snap)
    insert_synthetic_event(conn, snapshot_id=snap, event_id="evt_brain")

    rag = BrainBackroomRag(db_path=db_path, snapshot_id=snap)
    main_llm = ClaudeLLM(model=model, temperature=0.0)
    judge_llm = ClaudeLLM(
        model=model, temperature=0.0,
        system_prompt=PAIRWISE_JUDGE_PROMPT,
        cache_dir=os.path.expanduser("~/.cache/lpsf/claude_judge"),
    )

    try:
        candidates = rag.retrieve(query, limit=4)
        n_candidates = len(candidates)
        if n_candidates == 0:
            return {"query": query, "n_candidates": 0}

        rag_baseline = LLMPlusRAG()
        rerank = LLMPlusLPSFRerank(alpha=1.0, beta=1.0, gamma=1.0, judge_llm=judge_llm)

        r_rag = rag_baseline.respond(conn, query=query, snapshot_id=snap, llm=main_llm, rag=rag, seed=0)
        r_rr = rerank.respond(conn, query=query, snapshot_id=snap, llm=main_llm, rag=rag, seed=0)

        # Opaque ids only — strip the "path:" prefix to expose just the rowid.
        rag_pick = r_rag.selected_path.split(":")[-1]
        rr_pick = r_rr.selected_path.split(":")[-1]
        cost = (
            float(getattr(getattr(main_llm, "usage", None), "cost", lambda: 0.0)())
            + float(getattr(getattr(judge_llm, "usage", None), "cost", lambda: 0.0)())
        )
        return {
            "query": query,
            "n_candidates": n_candidates,
            "rag_pick_id": rag_pick,
            "rerank_pick_id": rr_pick,
            "diverged": rag_pick != rr_pick,
            "cost": cost,
        }
    finally:
        rag.close()
        conn.close()


def write_report(counts: Dict[str, int], rows: List[Dict[str, Any]], model: str, elapsed: float) -> None:
    lines = [
        "# LPSF Smoke Test on a Real 2nd-Brain FTS Index",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Safety note",
        "",
        "This report contains **only aggregate statistics and opaque note rowids**.",
        "No note titles, paths, or content are written here. Note summaries were",
        "sent to the LLM judge for ranking; per the 2nd-brain contract only",
        "non-high-sensitivity, external_llm-allowed notes pass the adapter gate.",
        "",
        "## Index gate",
        "",
        f"- Total notes in index: **{counts['total']}**",
        f"- Passing safety gate (sensitivity≠high, external_llm≠false): **{counts['safe']}**",
        f"- Gated out: **{counts['gated']}**",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        "- **Baselines:** LLMPlusRAG vs LLMPlusLPSFRerank (α=β=γ=1.0, no prior attractors)",
        "- **Queries:** generic technical topics (impersonal)",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
        "| Query | #candidates | RAG pick | Rerank pick | Diverged |",
        "|---|---:|---|---|---:|",
    ]
    for row in rows:
        if row["n_candidates"] == 0:
            lines.append(f"| {row['query']} | 0 | — | — | — |")
            continue
        lines.append(
            f"| {row['query']} | {row['n_candidates']} | "
            f"`#{row['rag_pick_id']}` | `#{row['rerank_pick_id']}` | "
            f"{'yes' if row['diverged'] else 'no'} |"
        )
    diverged = sum(1 for r in rows if r.get("diverged"))
    answered = sum(1 for r in rows if r.get("n_candidates", 0) > 0)
    lines += [
        "",
        "## Interpretation",
        "",
        f"- {answered}/{len(rows)} queries returned candidates from the real index.",
        f"- The LLM-judge rerank changed the RAG pick in {diverged}/{answered} answered queries.",
        "- With no prior attractors set (γ contributes 0 here), any divergence is purely",
        "  the LLM-judge channel re-ranking the BM25 winner. This validates that the",
        "  rerank pathway works end-to-end on a real, non-synthetic index.",
        "- A natural follow-up: set attractors from the user's actual past selections",
        "  and measure personalization — but that requires interaction history this",
        "  smoke test deliberately does not touch.",
        "",
        "_This is a plumbing smoke test, not a quality benchmark. It proves the real",
        "adapter retrieves, gates, and feeds the LPSF baselines correctly._",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="Path to a brain-backroom-style FTS index "
                             "(or set LPSF_BRAIN_FTS).")
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.db:
        print("ERROR: no index path. Pass --db /path/to/fts.db or set LPSF_BRAIN_FTS.")
        sys.exit(1)
    if not Path(args.db).exists():
        print(f"ERROR: index not found at {args.db}")
        sys.exit(1)

    from lpsf.experiments.brain_backroom_rag import BrainBackroomRag
    rag = BrainBackroomRag(db_path=args.db)
    counts = rag.safe_count()
    print(f"Index gate: total={counts['total']} safe={counts['safe']} gated={counts['gated']}")

    # Show retrieval candidate counts per query without any API calls.
    print("\nRetrieval probe (no API):")
    for q in QUERIES:
        n = len(rag.retrieve(q, limit=4))
        print(f"  {q!r}: {n} candidates")
    rag.close()

    if args.dry_run:
        print("\n=== DRY RUN — no LLM calls ===")
        return

    load_dotenv(REPO_ROOT / ".env.local")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print()
    rows = []
    total_cost = 0.0
    started = time.time()
    for q in QUERIES:
        t0 = time.time()
        print(f"{q!r} ...", end=" ", flush=True)
        out = run_query(args.db, q, args.model)
        rows.append(out)
        total_cost += out.get("cost", 0.0)
        if out["n_candidates"] == 0:
            print("no candidates")
        else:
            print(f"RAG=#{out['rag_pick_id']} RR=#{out['rerank_pick_id']} "
                  f"diverged={out['diverged']} ({time.time()-t0:.1f}s)")
    elapsed = time.time() - started
    write_report(counts, rows, args.model, elapsed)
    print(f"\nTotal cost: ${total_cost:.4f} | Wall: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
