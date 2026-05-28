#!/usr/bin/env python3
"""H6 adversarial, re-run with LLMPlusLPSFRerank.

The original H6 (with plain LLMPlusLPSF) showed that an attractor of depth 0.8
on ev:wrong (RAG score 0.20) overrides ev:correct (RAG score 0.90). This
worked because LLM output had no path to selection.

Now with LLMPlusLPSFRerank, the LLM acts as a pairwise judge with a
judgment-specific system prompt. The question: at what attractor depth does
LPSF still override the LLM's "correct" judgment?

Sweep across attractor strengths [0.5, 1.0, 2.0, 5.0] and temperatures
[0.0, 1.0] to map the LLM-judgment vs attractor frontier.

Cost: ~$0.05 (haiku, judge LLM).
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

ATTRACTOR_STRENGTH = 1.0  # max legal in one deepen call
BETAS = [0.0, 0.3, 0.6, 1.0, 2.0]
TEMPERATURES = [0.0, 1.0]
N_SEEDS = 5
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "H6_RERANK.md"


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


def run_cell(model: str, temperature: float, beta: float, seeds: range):
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusLPSFRerank
    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.hypotheses.h6_adversarial import build_rag_fixture
    from lpsf.experiments.mock_rag import MockRAG
    from lpsf.experiments.prompts import PAIRWISE_JUDGE_PROMPT
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )
    from lpsf.operators.deepen_attractor import deepen_attractor

    main_llm = ClaudeLLM(model=model, temperature=temperature)
    judge_llm = ClaudeLLM(model=model, temperature=temperature,
                          system_prompt=PAIRWISE_JUDGE_PROMPT,
                          cache_dir=os.path.expanduser("~/.cache/lpsf/claude_judge"))
    baseline = LLMPlusLPSFRerank(alpha=1.0, beta=beta, gamma=1.0, judge_llm=judge_llm)

    paths: List[str] = []
    for s in seeds:
        snap = f"snap_h6r_{model}_{temperature}_{beta}_{s}"
        evt = f"evt_h6r_{model}_{temperature}_{beta}_{s}"
        conn = db.init_db(":memory:")
        try:
            insert_synthetic_snapshot(conn, snapshot_id=snap)
            insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)
            deepen_attractor(
                conn,
                event_id=evt,
                snapshot_id=snap,
                target_type="path",
                target_id="path:ev:wrong",
                strength=ATTRACTOR_STRENGTH,
                half_life=3600,
                evidence_refs=["ev:wrong"],
                reason="h6 rerank sweep",
                scope="h6r",
            )
            rag = MockRAG(snapshot_id=snap, fixture=build_rag_fixture())
            resp = baseline.respond(
                conn, query="knowledge query", snapshot_id=snap,
                llm=main_llm, rag=rag, seed=s,
            )
            paths.append(resp.selected_path)
        finally:
            conn.close()

    main_cost = float(getattr(getattr(main_llm, "usage", None), "cost", lambda: 0.0)())
    judge_cost = float(getattr(getattr(judge_llm, "usage", None), "cost", lambda: 0.0)())
    return paths, main_cost + judge_cost


def write_report(rows: List[Dict], model: str, elapsed: float) -> None:
    lines = [
        "# H6 Adversarial under LLM-as-Reranker",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Question",
        "",
        "The original H6 showed that an attractor on `path:ev:wrong` (RAG=0.20, depth=0.8)",
        "overrode `path:ev:correct` (RAG=0.90) under the plain LLMPlusLPSF baseline.",
        "That worked because LLM output text was decoupled from selection.",
        "",
        "Now LLMPlusLPSFRerank adds the LLM as a pairwise judge with its own system prompt.",
        "We hold the attractor at the maximum legal strength (1.0) and sweep β (the weight",
        "on the LLM judgment channel) to find where LLM rerank starts saving the correct answer.",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        f"- **Baseline:** LLMPlusLPSFRerank with α=1.0, γ=1.0, β ∈ {BETAS}",
        "- **Judge LLM:** same model, PAIRWISE_JUDGE_PROMPT system prompt",
        "- **Fixture:** H6 — ev:correct (RAG 0.90), ev:wrong (RAG 0.20)",
        f"- **Attractor:** deepen path:ev:wrong with strength={ATTRACTOR_STRENGTH} (max legal)",
        f"- **Seeds:** {N_SEEDS} per cell",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
        "Cell shows the fraction of seeds where LPSF overrode (selected `path:ev:wrong`).",
        "0/N = LLM judge saved the correct answer. N/N = attractor still dominated.",
        "",
        "| β (LLM weight) | T=0.0 wrong-wins | T=1.0 wrong-wins |",
        "|---:|---:|---:|",
    ]
    by_cell: Dict = {}
    for row in rows:
        by_cell[(row["temperature"], row["beta"])] = row
    for beta in BETAS:
        cells = []
        for temp in TEMPERATURES:
            row = by_cell.get((temp, beta))
            if row is None:
                cells.append("—")
                continue
            wrong = sum(1 for p in row["paths"] if p == "path:ev:wrong")
            cells.append(f"{wrong}/{len(row['paths'])}")
        lines.append(f"| {beta:.2f} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- **β=0.0** = plain LPSF (LLM judgment disabled). Expected: wrong always wins,",
        "  reproducing the original H6 result.",
        "- **β high enough** = LLM judge wins. The β threshold at which the judge starts",
        "  protecting against the attractor is the operational tradeoff knob.",
        "",
        "## Amplitude math (for reference)",
        "",
        "    amp(correct) = α*0.90 + β*1   + γ*0      = 0.90 + β",
        "    amp(wrong)   = α*0.20 + β*0   + γ*1.0    = 1.20",
        "",
        "Judge always picks correct ⇒ correct wins iff `0.90 + β > 1.20` ⟺ `β > 0.30`.",
        "",
        "So we predict the flip happens at **β ≈ 0.30**: below that, attractor dominates;",
        "above, LLM judge saves the correct answer.",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seeds", type=int, default=N_SEEDS)
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env.local")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    from lpsf.experiments.cost import PRICING
    rates = PRICING.get(args.model, {"input": 0, "output": 0})
    cells = len(BETAS) * len(TEMPERATURES) * args.seeds
    total_calls = cells * 2  # main response + judge call
    print(f"Model: {args.model}")
    print(f"Betas: {BETAS}, Temps: {TEMPERATURES}, Seeds/cell: {args.seeds}")
    print(f"Estimated LLM calls: ~{total_calls}")
    print(f"Estimated cost: ~${total_calls * 80 * rates['output'] / 1_000_000:.4f}")
    if args.dry_run:
        print("=== DRY RUN ===")
        return

    print()
    rows = []
    total_cost = 0.0
    started = time.time()
    for temp in TEMPERATURES:
        for beta in BETAS:
            t0 = time.time()
            print(f"T={temp:.1f} beta={beta:.2f} ...", end=" ", flush=True)
            paths, cost = run_cell(args.model, temp, beta, range(args.seeds))
            total_cost += cost
            wrong_wins = sum(1 for p in paths if p == "path:ev:wrong")
            rows.append({"temperature": temp, "beta": beta, "paths": paths})
            print(f"wrong-wins={wrong_wins}/{len(paths)} ({time.time()-t0:.1f}s)")

    elapsed = time.time() - started
    write_report(rows, args.model, elapsed)
    print(f"\nTotal cost: ${total_cost:.4f} | Wall: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
