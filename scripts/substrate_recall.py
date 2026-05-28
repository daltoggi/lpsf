#!/usr/bin/env python3
"""Substrate recall experiment — the falsifiable test for "true memory".

Three systems share a FROZEN core and learn a stream of (key -> value) facts.
We then ask each, with an EMPTY input context, to recall the value for each
learned key. The question that separates true memory from fixed-dimension
search:

    Does the learned association live in PARAMETERS (recall works with empty
    context) or only in the INPUT (recall needs the value retrieved into
    context)?

Measured:
  1. empty-context recall accuracy  — the core test
  2. forgetting curve                — recall of ALL facts so far vs #facts
  3. parameter growth                — does capacity scale with experience?

numpy only, deterministic, $0. NOT a language model — see SUBSTRATE_NOTES.md.

Usage:
    python3 scripts/substrate_recall.py
    python3 scripts/substrate_recall.py --max-facts 60 --dim 64
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUTPUT = REPO_ROOT / "ops" / "lpsf" / "SUBSTRATE_RECALL.md"


def build_systems(core, n_values, seed):
    from lpsf.substrate import ExpandableMemory, FixedHebbian, FrozenRAG
    return [
        FrozenRAG(core, n_values, seed=seed),
        FixedHebbian(core, n_values, seed=seed),
        ExpandableMemory(core, n_values),
    ]


def forgetting_curve(max_facts: int, dim: int, seed: int):
    """For each prefix of facts, learn it fresh and measure empty-context
    recall over all facts learned so far. Returns {system: [(n, acc, params)]}."""
    from lpsf.substrate import FrozenCore

    checkpoints = sorted(set([2, 5, 10, 15, 20, 30, 40, 50, 60] + [max_facts]))
    checkpoints = [c for c in checkpoints if c <= max_facts]
    curves = {}

    for n in checkpoints:
        core = FrozenCore(n_concepts=max_facts, dim=dim, seed=seed)
        facts = [(k, k) for k in range(n)]  # distinct value per key
        for sysobj in build_systems(core, max_facts, seed):
            for k, v in facts:
                sysobj.learn(k, v)
            acc = float(np.mean([
                sysobj.recall(k, context_value=None) == v for k, v in facts
            ]))
            curves.setdefault(sysobj.name, []).append((n, acc, sysobj.param_count))
    return curves


def context_sanity(dim: int, seed: int):
    """Confirm FrozenRAG CAN answer when the value is in context (it just
    copies), proving its empty-context failure is about memory, not capability."""
    from lpsf.substrate import FrozenCore, FrozenRAG
    core = FrozenCore(n_concepts=10, dim=dim, seed=seed)
    rag = FrozenRAG(core, 10, seed=seed)
    with_ctx = float(np.mean([rag.recall(k, context_value=k) == k for k in range(10)]))
    without = float(np.mean([rag.recall(k, context_value=None) == k for k in range(10)]))
    return with_ctx, without


def render(curves, sanity, max_facts, dim, chance) -> str:
    names = {"frozen_rag": "Frozen + RAG", "fixed_hebbian": "Fixed Hebbian",
             "expandable": "Expandable"}
    final = {s: curves[s][-1] for s in curves}

    L = [
        "# Substrate Recall — the falsifiable test for memory-in-parameters",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        f"_numpy mechanism demo (NOT a language model); dim={dim}, up to {max_facts} facts, $0_",
        "",
        "## The test",
        "",
        "Learn `key -> value` facts, then recall each value with an **empty input",
        "context**. If recall works, the memory is in PARAMETERS (true memory). If",
        "it only works with the value retrieved into context, it's fixed-dimension",
        "search over inputs.",
        "",
        "## Final empty-context recall (all facts learned)",
        "",
        "| System | empty-ctx recall | params | params grow with experience? |",
        "|---|---:|---:|:--:|",
    ]
    grow = {"frozen_rag": "n/a (learns nothing)", "fixed_hebbian": "no — FIXED",
            "expandable": "yes — GROWS"}
    for s in ["frozen_rag", "fixed_hebbian", "expandable"]:
        n, acc, params = final[s]
        L.append(f"| {names[s]} | {acc:.3f} | {params} | {grow[s]} |")

    L += [
        "",
        f"_Chance baseline ≈ {chance:.3f} (1 / #values)._",
        "",
        "## Context sanity check",
        "",
        f"- Frozen+RAG **with** the value in context: recall = {sanity[0]:.3f} (it copies).",
        f"- Frozen+RAG **without** context: recall = {sanity[1]:.3f} (≈ chance).",
        "",
        "So Frozen+RAG is perfectly capable — it just has no memory in its",
        "parameters. Remove the context and the knowledge is gone. That is the",
        "hosted-API ceiling: you can never write a fact into the weights.",
        "",
        "## Forgetting curve (empty-context recall vs #facts learned)",
        "",
        "| #facts | Frozen+RAG | Fixed Hebbian | Expandable |",
        "|---:|---:|---:|---:|",
    ]
    # align by checkpoint index
    ref = curves["expandable"]
    for i in range(len(ref)):
        n = ref[i][0]
        row = [str(n)]
        for s in ["frozen_rag", "fixed_hebbian", "expandable"]:
            row.append(f"{curves[s][i][1]:.3f}")
        L.append("| " + " | ".join(row) + " |")

    L += [
        "",
        "## What this shows (and does not)",
        "",
        "- **Frozen+RAG never recalls with empty context.** No parameters change,",
        "  so no fact can live in the substrate. This is exactly a frozen LLM behind",
        "  an API: retrieval rearranges the input, the function is untouched.",
        "- **Fixed Hebbian recalls early but FORGETS as facts exceed its fixed",
        "  capacity.** A single d×d matrix has bounded storage; new facts overwrite",
        "  old ones through crosstalk. This is the 'fixed 12288-dimension' limit in",
        "  miniature.",
        "- **Expandable recalls everything because capacity GROWS with experience.**",
        "  Each distinct fact adds a parameter slot, so nothing is overwritten. This",
        "  is the mechanism that escapes a fixed dimension.",
        "",
        "**Honest scope:** this is a numpy associative-memory demo, not an LLM. It",
        "demonstrates the *mechanism* and its *necessity* (fixed capacity forgets;",
        "growth does not). It does NOT show this scales to a transformer, nor that a",
        "real model's pretrained knowledge survives such edits. The real-substrate",
        "step is an open-weights model with LoRA / activation-steering / expandable",
        "memory layers — see `docs/lpsf/SUBSTRATE_NOTES.md`.",
        "",
        "Reproduce: `python3 scripts/substrate_recall.py`",
    ]
    return "\n".join(L)


def main() -> None:
    parser = argparse.ArgumentParser()
    # Defaults chosen so #facts >> dim, making the fixed-capacity forgetting
    # of the Hebbian memory clearly visible against the expandable one.
    parser.add_argument("--max-facts", type=int, default=120)
    parser.add_argument("--dim", type=int, default=48)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    curves = forgetting_curve(args.max_facts, args.dim, args.seed)
    sanity = context_sanity(args.dim, args.seed)
    chance = 1.0 / args.max_facts

    text = render(curves, sanity, args.max_facts, args.dim, chance)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")

    # console summary
    print(f"{'system':16} {'empty-ctx@final':>16} {'params':>10} {'grows':>8}")
    print("-" * 56)
    grow = {"frozen_rag": "no", "fixed_hebbian": "no", "expandable": "YES"}
    for s in ["frozen_rag", "fixed_hebbian", "expandable"]:
        n, acc, params = curves[s][-1]
        print(f"{s:16} {acc:>16.3f} {params:>10} {grow[s]:>8}")
    print(f"\ncontext sanity: frozen_rag with-ctx={sanity[0]:.3f} without={sanity[1]:.3f}")
    print(f"Report: {OUTPUT}")


if __name__ == "__main__":
    main()
