#!/usr/bin/env python3
"""Rerank temperature sweep: now LLM noise actually enters path selection.

This is the experiment that the original temperature sensitivity could not
run, because the original LLMPlusLPSF baseline ignored LLM output for path
ranking. With the new LLMPlusLPSFRerank baseline (β > 0), the LLM vote on
candidate pairs is part of the selection equation.

For each temperature, runs a tied-RAG-score scenario where:
  - α = 1.0 (RAG weight, but tied so it cancels)
  - β = 1.0 (LLM vote weight)
  - γ ∈ {0.0, 0.5}  (attractor weight: off, then on)

Usage:
    python3 scripts/rerank_temp_sweep.py            # haiku, ~$0.10
    python3 scripts/rerank_temp_sweep.py --dry-run
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

TEMPERATURES = [0.0, 0.7, 1.0]
N_SEEDS = 10
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "RERANK_TEMP_SWEEP.md"


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


def build_world(snap: str, evt: str, *, gamma: float, attractor_target: str):
    from lpsf import db
    from lpsf.experiments.mock_rag import MockRAG
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )
    from lpsf.operators.deepen_attractor import deepen_attractor

    conn = db.init_db(":memory:")
    insert_synthetic_snapshot(conn, snapshot_id=snap)
    insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)
    if gamma > 0:
        deepen_attractor(
            conn,
            event_id=evt,
            snapshot_id=snap,
            target_type="path",
            target_id=attractor_target,
            strength=0.5,
            half_life=3600,
            evidence_refs=[attractor_target.split(":")[-1]],
            reason="rerank temp sweep anchor",
            scope="sweep",
        )
    rag = MockRAG(
        snapshot_id=snap,
        fixture={
            "best path": [
                {"id": "A", "score": 0.50, "sanitized_summary": "candidate A"},
                {"id": "B", "score": 0.50, "sanitized_summary": "candidate B"},
            ],
        },
    )
    return conn, rag


def run_temp(llm_cls, model: str, temperature: float, gamma: float, seeds: range):
    from lpsf.experiments.baselines import LLMPlusLPSFRerank

    llm = llm_cls(model=model, temperature=temperature)
    baseline = LLMPlusLPSFRerank(alpha=1.0, beta=1.0, gamma=gamma)
    paths: List[str] = []
    for s in seeds:
        snap = f"snap_rrtemp_{model}_{temperature}_{gamma}_{s}"
        evt = f"evt_rrtemp_{model}_{temperature}_{gamma}_{s}"
        conn, rag = build_world(snap, evt, gamma=gamma, attractor_target="path:B")
        try:
            resp = baseline.respond(
                conn, query="best path", snapshot_id=snap, llm=llm, rag=rag, seed=s
            )
            paths.append(resp.selected_path)
        finally:
            conn.close()
    cost = float(getattr(getattr(llm, "usage", None), "cost", lambda: 0.0)())
    return paths, cost


def write_report(rows: List[Dict], model: str, elapsed: float) -> None:
    lines = [
        "# LPSF LLM-as-Reranker Temperature Sweep",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Question",
        "",
        "With `LLMPlusLPSFRerank` (β>0), LLM output text **does** affect path",
        "selection via pairwise voting. Does temperature now produce variance,",
        "and does the LPSF attractor (γ>0) reduce that variance?",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        f"- **Baseline:** LLMPlusLPSFRerank with α=1.0, β=1.0, γ ∈ {{0.0, 0.5}}",
        "- **Fixture:** tied RAG scores (ev:A = ev:B = 0.50)",
        "- **Attractor:** when γ>0, deepen path:B with strength 0.5",
        f"- **Seeds:** {N_SEEDS} per cell",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
        "| Temperature | γ (attractor weight) | Distinct paths | Paths observed |",
        "|---:|---:|---:|---|",
    ]
    for row in rows:
        unique = sorted(set(row["paths"]))
        lines.append(
            f"| {row['temperature']:.1f} | {row['gamma']:.1f} | "
            f"{len(unique)} | "
            f"{', '.join(f'`{p}`' for p in unique)} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Compare γ=0 (no LPSF) vs γ=0.5 (LPSF on path:B) at each temperature:",
        "",
        "- **γ=0 high-temp distinct > γ=0.5 high-temp distinct** → LPSF reduces variance under LLM noise.",
        "  The 'attractor as anchor in stochastic LLM' thesis, now properly testable.",
        "- **γ=0 and γ=0.5 give same distinct count** → Attractor doesn't help against current LLM noise level.",
        "  Either the attractor depth is too small relative to LLM vote, or the model is too consistent.",
        "- **γ=0 distinct = 1 even at temp=1.0** → Haiku/Sonnet pairwise voting is robust to temperature.",
        "  We'd need to either crank β much higher or use a smaller/weaker model.",
        "",
        "Whatever the result, this is the first experiment where LLM temperature actually has",
        "a causal path to selected_path. The earlier temperature sweep (with plain LLMPlusLPSF)",
        "could not produce variance because LLM output was architecturally decoupled from selection.",
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

    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.cost import PRICING

    rates = PRICING.get(args.model, {"input": 0, "output": 0})
    total_calls = len(TEMPERATURES) * 2 * args.seeds * 2  # 2 LLM calls per respond
    print(f"Model: {args.model}")
    print(f"Temperatures: {TEMPERATURES}, gamma in [0.0, 0.5]")
    print(f"Seeds per cell: {args.seeds}")
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
        for gamma in [0.0, 0.5]:
            t0 = time.time()
            print(f"temp={temp:.1f} gamma={gamma:.1f} ...", end=" ", flush=True)
            paths, cost = run_temp(
                ClaudeLLM, args.model, temp, gamma, range(args.seeds)
            )
            total_cost += cost
            unique = sorted(set(paths))
            rows.append({"temperature": temp, "gamma": gamma, "paths": paths})
            print(f"distinct={len(unique)} ({time.time()-t0:.1f}s)")

    elapsed = time.time() - started
    write_report(rows, args.model, elapsed)
    print(f"\nTotal cost: ${total_cost:.4f} | Wall: {elapsed:.1f}s")

    print(f"\n{'temp':>6} {'gamma':>6} | {'distinct':>8} | paths")
    print("-" * 60)
    for row in rows:
        unique = sorted(set(row["paths"]))
        print(f"{row['temperature']:>6.1f} {row['gamma']:>6.1f} | {len(unique):>8} | {unique}")


if __name__ == "__main__":
    main()
