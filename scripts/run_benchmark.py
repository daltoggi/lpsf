#!/usr/bin/env python3
"""LPSF M4 Phase 3 benchmark runner.

Usage:
    python3 scripts/run_benchmark.py --mode smoke           # ~$0.05
    python3 scripts/run_benchmark.py --mode standard        # ~$2-4
    python3 scripts/run_benchmark.py --mode standard --dry-run    # no API calls

Loads API keys from environment OR .env.local (gitignored). Writes
EVALUATION_REPORT.md and EVALUATION_REPORT.json under ops/lpsf/.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE per line, # comments, no quotes parsing.

    Sets the env var if currently missing OR empty. The harness may pre-set
    API key vars to empty strings as a safety default; we treat empty as
    "not set" and let the .env.local value through.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not os.environ.get(key):  # missing OR empty
            os.environ[key] = value


def build_llms(mode: str, temperature: float = 0.0):
    """Return list of (display_name, llm_instance) pairs for the given mode."""
    from lpsf.experiments.claude_llm import ClaudeLLM
    from lpsf.experiments.openai_llm import OpenAILLM

    llms = []
    if mode == "smoke":
        llms.append(("claude-haiku-4-5", ClaudeLLM(model="claude-haiku-4-5", temperature=temperature)))
    elif mode == "standard":
        llms.append(("claude-sonnet-4-5", ClaudeLLM(model="claude-sonnet-4-5", temperature=temperature)))
        if os.environ.get("OPENAI_API_KEY"):
            llms.append(("gpt-4o", OpenAILLM(model="gpt-4o", temperature=temperature)))
        else:
            print("WARNING: OPENAI_API_KEY not set; running Claude-only standard.")
    elif mode == "thorough":
        llms.append(("claude-sonnet-4-5", ClaudeLLM(model="claude-sonnet-4-5", temperature=temperature)))
        llms.append(("claude-opus-4-7", ClaudeLLM(model="claude-opus-4-7", temperature=temperature)))
        if os.environ.get("OPENAI_API_KEY"):
            llms.append(("gpt-4o", OpenAILLM(model="gpt-4o", temperature=temperature)))
    else:
        raise ValueError(f"Unknown mode: {mode}")
    return llms


def mode_config(mode: str):
    """Return (hypotheses, seeds, baselines, budget_cap) for the mode."""
    base_hypotheses = (
        "H1_before_after",
        "H3_privacy_safety",
        "H4_snapshot_reproducibility",
        "H5_tension_register",
    )
    base_baselines = ("LLMOnly", "LLMPlusRAG", "LLMPlusLPSF")
    if mode == "smoke":
        return base_hypotheses, (0,), base_baselines, 0.50
    if mode == "standard":
        return base_hypotheses, tuple(range(10)), base_baselines, 5.00
    if mode == "thorough":
        return base_hypotheses, tuple(range(30)), base_baselines, 30.00
    raise ValueError(f"Unknown mode: {mode}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "standard", "thorough"], default="smoke")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and exit without calling APIs")
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "ops" / "lpsf"))
    parser.add_argument("--budget-override", type=float, default=None, help="Override budget cap (USD)")
    parser.add_argument("--temperature", type=float, default=0.0, help="LLM sampling temperature (0.0 = deterministic)")
    parser.add_argument("--hypotheses", default=None, help="Comma-separated subset of hypotheses, e.g. H1_before_after,H4_snapshot_reproducibility")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env.local")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in env or .env.local")
        sys.exit(1)

    hypotheses, seeds, baselines, budget = mode_config(args.mode)
    if args.budget_override is not None:
        budget = args.budget_override
    if args.hypotheses:
        hypotheses = tuple(h.strip() for h in args.hypotheses.split(",") if h.strip())

    print(f"Mode: {args.mode}")
    print(f"Temperature: {args.temperature}")
    print(f"Hypotheses: {hypotheses}")
    print(f"Seeds: {len(seeds)} per (model × hypothesis)")
    print(f"Baselines: {baselines}")
    print(f"Budget cap: ${budget:.2f}")

    if args.dry_run:
        from lpsf.experiments.cost import PRICING
        print("\n=== DRY RUN ===")
        print("Models in plan (no calls will be made):")
        llms = build_llms(args.mode, temperature=args.temperature)
        for name, llm in llms:
            rates = PRICING.get(llm.version(), {"input": 0, "output": 0})
            print(f"  - {name}: ${rates['input']}/M input, ${rates['output']}/M output")
        total_calls = len(llms) * len(hypotheses) * len(seeds)
        print(f"Total LLM calls (worst-case, no cache): ~{total_calls * 6}")
        print(f"(6 = avg queries × baselines per scenario; H1 has 8, H3 has 4, H4 has 1, H5 has 1)")
        return

    llms = build_llms(args.mode, temperature=args.temperature)
    print(f"Active LLMs: {[name for name, _ in llms]}\n")

    from lpsf.experiments.benchmark import run_benchmark
    from lpsf.experiments.report import render_report, report_to_json

    started = time.time()
    report = run_benchmark(
        llms=llms,
        hypotheses=hypotheses,
        seeds=seeds,
        baselines=baselines,
        budget_usd=budget,
        progress=True,
    )
    elapsed = time.time() - started

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "EVALUATION_REPORT.md"
    json_path = output_dir / "EVALUATION_REPORT.json"

    md_path.write_text(render_report(report), encoding="utf-8")
    json_path.write_text(report_to_json(report), encoding="utf-8")

    print(f"\n=== DONE ===")
    print(f"Wall time: {elapsed:.1f}s")
    summary = report.cost_summary()
    print(f"Total cost: ${summary['total_estimated_cost_usd']:.4f}")
    print(f"Total calls: {summary['total_calls']} (cache hits: {summary['total_cache_hits']})")
    print(f"Passed: {report.passed_count()}/{len(report.results)}")
    print(f"Report: {md_path}")
    print(f"JSON:   {json_path}")


if __name__ == "__main__":
    main()
