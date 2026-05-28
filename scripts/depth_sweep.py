#!/usr/bin/env python3
"""Attractor depth sweep: find the noise-tolerance threshold.

Varies deepen_attractor strength in H4_snapshot_reproducibility at
temperature=1.0 (max noise). Measures how many distinct LLMPlusLPSF
paths appear as depth weakens.

Expected behavior:
  - High depth  → 1 distinct path  (attractor fully dominates)
  - Low depth   → many paths       (LLM noise overrides attractor)
  - Threshold   → where convergence first breaks down

Usage:
    python3 scripts/depth_sweep.py             # default haiku + depths
    python3 scripts/depth_sweep.py --dry-run
    python3 scripts/depth_sweep.py --model claude-sonnet-4-5

Estimated cost: ~$0.05–0.10 (haiku, 6 depths × 10 seeds × temp=1.0)
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

DEPTHS = [0.05, 0.10, 0.20, 0.40, 0.60, 0.80]
TEMPERATURE = 1.0
N_SEEDS = 10
BASELINES = ("LLMPlusRAG", "LLMPlusLPSF")
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "DEPTH_SWEEP.md"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if not os.environ.get(key.strip()):
            os.environ[key.strip()] = value.strip()


def _h4_scenario_with_depth(snapshot_id: str, event_id: str, depth: float) -> dict:
    """H4 scenario with configurable attractor depth."""
    return {
        "queries": [{"phase": "main", "query": "memory question for replay", "query_id": "h4_q_main"}],
        "operations": [
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:M1",
                    "strength": depth,
                    "half_life": 3600,
                    "evidence_refs": ["ev:M1"],
                    "reason": f"depth_sweep depth={depth}",
                    "scope": "h4",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["memory"],
            "available_evidence_ids": ["ev:M1", "ev:M2"],
            "active_attractor_paths": ["path:ev:M1"],
            "forbidden_patterns": [],
        },
    }


def _h4_verify(result: dict) -> Tuple[bool, List[str]]:
    return (bool(result.get("phase_results")), [])


def run_depth(llm_cls, model: str, depth: float, seeds: range) -> Tuple[int, int, List[str], float]:
    """Returns (pass_count, total, lpsf_paths, cost)."""
    from lpsf import db
    from lpsf.experiments.mock_rag import MockRAG
    from lpsf.experiments.runner import run_experiment
    from lpsf.experiments.scenarios import (
        default_rag_fixture,
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )

    llm = llm_cls(model=model, temperature=TEMPERATURE)
    lpsf_paths: List[str] = []
    passed = 0
    total = 0

    for seed in seeds:
        snap = f"snap_depth_{depth}_{seed}"
        evt = f"evt_depth_{depth}_{seed}"
        conn = db.init_db(":memory:")
        try:
            insert_synthetic_snapshot(conn, snapshot_id=snap)
            insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)
            rag = MockRAG(snapshot_id=snap, fixture=default_rag_fixture())
            scenario = _h4_scenario_with_depth(snap, evt, depth)
            result = run_experiment(
                conn,
                hypothesis_name="H4_depth_sweep",
                scenario=scenario,
                baselines=BASELINES,
                snapshot_id=snap,
                llm=llm,
                rag=rag,
                event_id=evt,
                seed=seed,
                verify=_h4_verify,
            )
            total += 1
            if result["passed"]:
                passed += 1
            for phase, by_baseline in result["phase_results"].items():
                if "LLMPlusLPSF" in by_baseline:
                    lpsf_paths.append(by_baseline["LLMPlusLPSF"].selected_path)
        finally:
            conn.close()

    cost = float(getattr(getattr(llm, "usage", None), "cost", lambda: 0.0)())
    return passed, total, lpsf_paths, cost


def write_report(rows: List[Dict], model: str, elapsed: float) -> None:
    lines = [
        "# LPSF Attractor Depth Sweep",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        f"- **Temperature:** {TEMPERATURE} (maximum noise)",
        f"- **Seeds:** {N_SEEDS} per depth",
        f"- **Baselines:** {', '.join(BASELINES)}",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
        "| Attractor depth | Distinct LLMPlusLPSF paths | Pass rate | Paths observed |",
        "|---:|---:|---:|---|",
    ]
    threshold_found = False
    for row in rows:
        unique = sorted(set(row["paths"]))
        converged = "✓" if len(unique) == 1 else "✗"
        if len(unique) > 1 and not threshold_found:
            threshold_found = True
            converged = "← threshold"
        lines.append(
            f"| {row['depth']:.2f} | {len(unique)} | "
            f"{row['passed']}/{row['total']} | "
            f"{', '.join(f'`{p}`' for p in unique[:4])} {converged} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- **Depth where distinct paths = 1**: attractor dominates noise.",
        "- **Threshold**: lowest depth where convergence holds at temperature=1.0.",
        "- A threshold > 0.3 suggests that practical deployments need moderate",
        "  attractor depth to stay robust across repeated LLM draws.",
        "",
        "_Run with `scripts/depth_sweep.py` to update._",
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
    total_calls = len(DEPTHS) * args.seeds * len(BASELINES)
    print(f"Model: {args.model} (temp={TEMPERATURE})")
    print(f"Depths: {DEPTHS}")
    print(f"Seeds per depth: {args.seeds}")
    print(f"Estimated calls: ~{total_calls}")
    print(f"Estimated cost: ~${total_calls * 100 * rates['output'] / 1_000_000:.4f}")

    if args.dry_run:
        print("\n=== DRY RUN ===")
        return

    rows = []
    total_cost = 0.0
    started = time.time()
    print()

    for depth in DEPTHS:
        t0 = time.time()
        print(f"depth={depth:.2f} ...", end=" ", flush=True)
        passed, total, paths, cost = run_depth(ClaudeLLM, args.model, depth, range(args.seeds))
        total_cost += cost
        unique = sorted(set(paths))
        rows.append({"depth": depth, "passed": passed, "total": total, "paths": paths})
        print(f"distinct={len(unique)} pass={passed}/{total} cost=${cost:.4f} ({time.time()-t0:.1f}s)")

    elapsed = time.time() - started
    write_report(rows, args.model, elapsed)
    print(f"\nTotal cost: ${total_cost:.4f} | Wall: {elapsed:.1f}s")

    print(f"\n{'Depth':>8} | {'Distinct':>8} | Paths")
    print("-" * 55)
    for row in rows:
        unique = sorted(set(row["paths"]))
        print(f"{row['depth']:>8.2f} | {len(unique):>8} | {unique}")


if __name__ == "__main__":
    main()
