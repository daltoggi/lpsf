#!/usr/bin/env python3
"""Personalization demo — experience changes the landscape, persisted.

Runs the full loop on the committed demo corpus with MockLLM ($0):
  1. search "local data storage" → RAG ranking
  2. user picks sqlite a few times
  3. search again → sqlite is now ranked #1 by accumulated attractor depth
  4. reopen the state DB → personalization persisted

Writes ops/lpsf/PERSONALIZATION_DEMO.md with the captured transcript.
"""

from __future__ import annotations

import datetime
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

CORPUS = REPO_ROOT / "data" / "corpus.fts.db"
OUTPUT = REPO_ROOT / "ops" / "lpsf" / "PERSONALIZATION_DEMO.md"
QUERY = "local data storage"
PICK = "01_sqlite_for_apps"
N_PICKS = 3


def _fmt(results) -> str:
    lines = [f"{'#':>2}  {'id':24} {'amp':>7} {'rag':>6} {'attr':>6} {'picks':>5}"]
    lines.append("-" * 60)
    for r in results:
        lines.append(
            f"{r.rank:>2}  {r.evidence_id:24} {r.amplitude:>7.3f} "
            f"{r.rag_score:>6.3f} {r.attractor_depth:>6.3f} {r.picked_before:>5}"
        )
    return "\n".join(lines)


def run() -> str:
    from lpsf.app import LPSFSearchSession
    from lpsf.experiments.local_fts_rag import LocalFTSRag
    from lpsf.experiments.mock_llm import MockLLM

    tmp = Path(tempfile.mkdtemp()) / "demo_state.db"
    blocks = []

    rag = LocalFTSRag(db_path=str(CORPUS), snapshot_id="app_v1")
    sess = LPSFSearchSession(state_db_path=str(tmp), rag=rag, llm=MockLLM(seed=0))

    blocks.append(("Step 1 — initial search (no history)", _fmt(sess.search(QUERY, limit=3))))

    for _ in range(N_PICKS):
        sess.record_pick(PICK, query=QUERY)
    blocks.append((
        f"Step 2 — user picks `{PICK}` {N_PICKS}× (each deepens its attractor)",
        f"(attractor depth on path:{PICK} accumulates by pick_strength per pick)",
    ))

    blocks.append((
        "Step 3 — same search, now personalized",
        _fmt(sess.search(QUERY, limit=3)),
    ))
    sess.close()

    # Reopen to show persistence
    rag2 = LocalFTSRag(db_path=str(CORPUS), snapshot_id="app_v1")
    sess2 = LPSFSearchSession(state_db_path=str(tmp), rag=rag2, llm=MockLLM(seed=0))
    blocks.append((
        "Step 4 — fresh process over the same on-disk state (persistence)",
        _fmt(sess2.search(QUERY, limit=3)),
    ))
    sess2.close()
    tmp.unlink(missing_ok=True)

    md = [
        "# LPSF Personalization Demo",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        "_Demo corpus, MockLLM, $0 — fully reproducible via "
        "`python3 scripts/personalization_demo.py`._",
        "",
        "This is the honest realization of the original LPSF vision: a system",
        "whose response landscape changes after experience. Here, *experience*",
        "= the user's picks, and *landscape change* = a persistent reranking",
        "prior. No LLM internals are modified; the mechanism is an auditable",
        "additive attractor over retrieval candidates.",
        "",
    ]
    for title, body in blocks:
        md.append(f"## {title}")
        md.append("")
        md.append("```")
        md.append(body)
        md.append("```")
        md.append("")
    md += [
        "## What to notice",
        "",
        f"- Initially `04_local_first` outranks `{PICK}` on BM25 alone.",
        f"- After {N_PICKS} picks, `{PICK}`'s accumulated attractor depth lifts it to #1.",
        "- The ranking change survives a process restart — it's on disk.",
        "- Every pick is an `experience_event` row; every nudge is a "
        "`plasticity_mark` row; the boost is `rag_score + attractor_depth`. "
        "Nothing is hidden.",
        "",
        "Try it live:",
        "",
        "```bash",
        'python3 scripts/lpsf_search.py search "local data storage"',
        'python3 scripts/lpsf_search.py pick 01_sqlite_for_apps -q "local data storage"',
        'python3 scripts/lpsf_search.py search "local data storage"   # sqlite now #1',
        'python3 scripts/lpsf_search.py why "local data storage"       # see the math',
        "```",
    ]
    text = "\n".join(md)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    out = run()
    print(out)
    print(f"\n[written to {OUTPUT}]")
