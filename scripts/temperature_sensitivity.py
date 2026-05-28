#!/usr/bin/env python3
"""Temperature sensitivity experiment for H4_snapshot_reproducibility.

Tests whether LPSF's attractor depth genuinely dominates over LLM sampling
noise, or whether the 100% reproducibility in standard runs was a
temperature=0.0 artifact.

For each temperature in TEMPERATURES:
  - Run H4_snapshot_reproducibility with N_SEEDS seeds
  - Count distinct selected_paths for LLMPlusLPSF
  - Expected: low temperature → 1 distinct path; high temperature → more paths
    IF the LPSF state truly dominates attractor alignment should hold regardless

Usage:
    python3 scripts/temperature_sensitivity.py             # claude-haiku-4-5
    python3 scripts/temperature_sensitivity.py --dry-run   # cost estimate only
    python3 scripts/temperature_sensitivity.py --model claude-sonnet-4-5

Estimated cost: ~$0.01–0.05 for default (haiku, 10 seeds, 3 temps)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

TEMPERATURES = [0.0, 0.7, 1.0]
N_SEEDS = 10
HYPOTHESIS = "H4_snapshot_reproducibility"
BASELINES = ("LLMOnly", "LLMPlusRAG", "LLMPlusLPSF")
OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "TEMPERATURE_SENSITIVITY.md"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not os.environ.get(key):
            os.environ[key] = value.strip()


def run_one_temperature(
    llm_cls,
    model: str,
    temperature: float,
    seeds: range,
) -> Tuple[List[bool], List[str], float]:
    """Run H4 for all seeds at one temperature. Returns (passed_list, lpsf_paths, cost)."""
    from lpsf.experiments.benchmark import run_benchmark
    from lpsf.experiments.cost import TokenUsage

    llm = llm_cls(model=model, temperature=temperature)
    report = run_benchmark(
        llms=[(model, llm)],
        hypotheses=[HYPOTHESIS],
        seeds=tuple(seeds),
        baselines=BASELINES,
        budget_usd=2.0,
        progress=False,
    )
    passed = [r.passed for r in report.results]
    lpsf_paths: List[str] = []
    for r in report.results:
        for phase, by_baseline in r.selected_paths_by_phase.items():
            if "LLMPlusLPSF" in by_baseline:
                lpsf_paths.append(by_baseline["LLMPlusLPSF"])
    cost = report.cost_summary()["total_estimated_cost_usd"]
    return passed, lpsf_paths, float(cost)


def render_table(rows: List[Dict]) -> str:
    lines = [
        "| Temperature | Pass rate | Distinct LLMPlusLPSF paths | Paths observed |",
        "|---:|---:|---:|---|",
    ]
    for row in rows:
        unique = sorted(set(row["paths"]))
        lines.append(
            f"| {row['temperature']:.1f} | "
            f"{row['pass_count']}/{row['total']} ({row['pass_count']/max(row['total'],1)*100:.0f}%) | "
            f"{len(unique)} | "
            f"{', '.join(f'`{p}`' for p in unique[:5])} |"
        )
    return "\n".join(lines)


def write_report(rows: List[Dict], model: str, elapsed: float) -> str:
    import datetime
    lines = [
        "# LPSF Temperature Sensitivity Report",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Setup",
        "",
        f"- **Model:** {model}",
        f"- **Hypothesis:** {HYPOTHESIS}",
        f"- **Seeds:** {N_SEEDS} per temperature",
        f"- **Baselines:** {', '.join(BASELINES)}",
        f"- **Wall time:** {elapsed:.1f}s",
        "",
        "## Results",
        "",
        render_table(rows),
        "",
        "## Interpretation",
        "",
        "- **1 distinct path at all temperatures** → LPSF attractor depth genuinely dominates sampling noise.",
        "  The standard-run reproducibility was not a temperature=0 artifact.",
        "- **1 distinct path only at temperature=0** → The reproducibility was a determinism artifact.",
        "  LPSF state alone is not sufficient to overcome LLM variance.",
        "- **Increasing distinct paths with temperature** → LLM noise partially overrides attractor alignment.",
        "  Increasing attractor depth (via `deepen_attractor` operator) may restore convergence.",
        "",
        "_This experiment was designed to validate (or refute) the H4 reproducibility claim from the",
        "standard-mode run, where temperature=0 made the result trivially deterministic._",
    ]
    text = "\n".join(lines)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seeds", type=int, default=N_SEEDS)
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env.local")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in env or .env.local")
        sys.exit(1)

    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.cost import PRICING

    rates = PRICING.get(args.model, {"input": 0, "output": 0})
    total_calls = len(TEMPERATURES) * args.seeds * 3  # ~3 LLM calls per scenario/baseline
    print(f"Model: {args.model} (${rates['input']}/M input, ${rates['output']}/M output)")
    print(f"Temperatures: {TEMPERATURES}")
    print(f"Seeds per temp: {args.seeds}")
    print(f"Estimated LLM calls: ~{total_calls}")
    print(f"Estimated cost: ~${total_calls * 100 * rates['output'] / 1_000_000:.4f} (rough upper bound)")

    if args.dry_run:
        print("\n=== DRY RUN — no API calls made ===")
        return

    print()
    total_cost = 0.0
    rows = []
    started = time.time()

    for temp in TEMPERATURES:
        t0 = time.time()
        print(f"Running temperature={temp:.1f} ...", end=" ", flush=True)
        passed, paths, cost = run_one_temperature(
            ClaudeLLM, args.model, temp, range(args.seeds)
        )
        elapsed = time.time() - t0
        total_cost += cost
        unique = sorted(set(paths))
        rows.append({
            "temperature": temp,
            "pass_count": sum(passed),
            "total": len(passed),
            "paths": paths,
        })
        print(f"done ({elapsed:.1f}s) pass={sum(passed)}/{len(passed)} distinct_paths={len(unique)} cost=${cost:.4f}")

    elapsed_total = time.time() - started
    write_report(rows, args.model, elapsed_total)

    print(f"\n=== DONE ===")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Wall time: {elapsed_total:.1f}s")
    print(f"Report: {OUTPUT_PATH}")

    print(f"\n{'Temperature':>12} | {'Pass rate':>10} | {'Distinct paths':>16} | Paths")
    print("-" * 70)
    for row in rows:
        unique = sorted(set(row["paths"]))
        print(
            f"{row['temperature']:>12.1f} | "
            f"{row['pass_count']}/{row['total']:>2}       | "
            f"{len(unique):>16} | {unique}"
        )


if __name__ == "__main__":
    main()
