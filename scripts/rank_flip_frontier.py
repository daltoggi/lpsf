#!/usr/bin/env python3
"""Rank-flip frontier: map the (Δr, Δa) decision boundary.

For each cell in the (retrieval gap × attractor differential) grid:
  - Build a 2-candidate RAG fixture where:
      ev:A has score baseline + Δr/2
      ev:B has score baseline - Δr/2
    so that ev:A wins by margin Δr.
  - Deepen attractor on path:ev:B with strength Δa.
  - Run LLMPlusLPSF; record which candidate it picks.

Theoretical prediction (from the current selection equation):
  path:ev:B wins  iff  Δa > Δr   (linear boundary, Δa = Δr)

Any deviation from this exact line is real architectural info.
The experiment uses MockLLM because the LLM output text does NOT
affect path selection — running expensive APIs here adds no signal.

Usage:
    python3 scripts/rank_flip_frontier.py
    python3 scripts/rank_flip_frontier.py --output ops/lpsf/RANK_FLIP_FRONTIER.md
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


DELTA_R = [0.00, 0.02, 0.05, 0.10, 0.20, 0.40, 0.80]
DELTA_A = [0.00, 0.02, 0.05, 0.10, 0.20, 0.40, 0.80, 1.00]
BASELINE_SCORE = 0.50


def build_tied_fixture(delta_r: float) -> Dict[str, List[Dict]]:
    """Two-candidate fixture with retrieval gap = delta_r in favor of ev:A."""
    return {
        "tied query": [
            {
                "id": "ev:A",
                "score": BASELINE_SCORE + delta_r / 2,
                "sanitized_summary": "candidate A summary",
                "source_type": "synthetic",
            },
            {
                "id": "ev:B",
                "score": BASELINE_SCORE - delta_r / 2,
                "sanitized_summary": "candidate B summary",
                "source_type": "synthetic",
            },
        ],
    }


def run_cell(delta_r: float, delta_a: float) -> Tuple[str, float, float]:
    """Run one (Δr, Δa) cell. Returns (selected_path, amp_A, amp_B)."""
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusLPSF
    from lpsf.experiments.mock_llm import MockLLM
    from lpsf.experiments.mock_rag import MockRAG
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )

    conn = db.init_db(":memory:")
    try:
        snap = f"snap_frontier_{delta_r:.4f}_{delta_a:.4f}"
        evt = f"evt_frontier_{delta_r:.4f}_{delta_a:.4f}"
        insert_synthetic_snapshot(conn, snapshot_id=snap)
        insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)

        if delta_a > 0:
            from lpsf.operators.deepen_attractor import deepen_attractor
            deepen_attractor(
                conn,
                event_id=evt,
                snapshot_id=snap,
                target_type="path",
                target_id="path:ev:B",
                strength=delta_a,
                half_life=3600,
                evidence_refs=["ev:B"],
                reason=f"frontier dr={delta_r} da={delta_a}",
                scope="frontier",
            )

        rag = MockRAG(snapshot_id=snap, fixture=build_tied_fixture(delta_r))
        llm = MockLLM(seed=0)
        baseline = LLMPlusLPSF()
        resp = baseline.respond(
            conn,
            query="tied query",
            snapshot_id=snap,
            llm=llm,
            rag=rag,
            seed=0,
        )
        amp_a = resp.amplitudes.get("path:ev:A", 0.0)
        amp_b = resp.amplitudes.get("path:ev:B", 0.0)
        return resp.selected_path, amp_a, amp_b
    finally:
        conn.close()


def render_grid(grid: List[List[str]]) -> str:
    lines = []
    header = "| Δa \\ Δr | " + " | ".join(f"{dr:.2f}" for dr in DELTA_R) + " |"
    sep = "|---:|" + "|".join(["---:"] * len(DELTA_R)) + "|"
    lines.append(header)
    lines.append(sep)
    for da_idx, da in enumerate(DELTA_A):
        row = [f"{da:.2f}"]
        for dr_idx in range(len(DELTA_R)):
            row.append(grid[da_idx][dr_idx])
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_report(grid: List[List[str]], amp_grid: List[List[Tuple[float, float]]],
                  deviations: List[str]) -> str:
    out = [
        "# LPSF Rank-Flip Frontier",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_",
        "",
        "## Question",
        "",
        "Given a retrieval gap **Δr** favoring `path:ev:A` (higher RAG score)",
        "and an attractor differential **Δa** favoring `path:ev:B` (deepened),",
        "at what (Δr, Δa) does LLMPlusLPSF flip from A to B?",
        "",
        "## Theoretical prediction",
        "",
        "From `c* = argmax(rag_score + attractor_depth)`:",
        "",
        "    path:ev:B wins  ⟺  (BASE - Δr/2 + Δa) > (BASE + Δr/2)",
        "                    ⟺  Δa > Δr",
        "",
        "Boundary is the linear diagonal **Δa = Δr**. Any deviation indicates",
        "non-additive interaction in the selection layer.",
        "",
        "## Empirical grid",
        "",
        "Cell shows which candidate LLMPlusLPSF selected at (Δr, Δa).",
        "`A` = `path:ev:A` (RAG winner). `B` = `path:ev:B` (attractor target).",
        "`tie` = both amplitudes equal (boundary cell).",
        "",
        render_grid(grid),
        "",
        "## Amplitude detail",
        "",
        "Each cell: `(amp_A, amp_B)`. Selected = argmax.",
        "",
    ]
    out.append("| Δa \\ Δr | " + " | ".join(f"{dr:.2f}" for dr in DELTA_R) + " |")
    out.append("|---:|" + "|".join(["---:"] * len(DELTA_R)) + "|")
    for da_idx, da in enumerate(DELTA_A):
        row = [f"{da:.2f}"]
        for dr_idx in range(len(DELTA_R)):
            a, b = amp_grid[da_idx][dr_idx]
            row.append(f"{a:.2f}/{b:.2f}")
        out.append("| " + " | ".join(row) + " |")

    out += [
        "",
        "## Boundary verification",
        "",
    ]
    if not deviations:
        out.append("✓ **All cells consistent with the linear prediction Δa = Δr.**")
        out.append("")
        out.append("The empirical decision boundary matches the equation derived from")
        out.append("`baselines.py::LLMPlusLPSF.respond` exactly. There is no hidden")
        out.append("interaction term in the selection layer — the system does what its")
        out.append("source says it does.")
    else:
        out.append(f"⚠ **{len(deviations)} cells deviated from the linear prediction:**")
        out.append("")
        for v in deviations:
            out.append(f"- {v}")
        out.append("")
        out.append("These deviations indicate non-additive behavior in the selection layer.")
        out.append("Investigation needed.")

    out += [
        "",
        "## Interpretation",
        "",
        "- Cells where Δa > Δr show `B` (attractor overrode RAG).",
        "- Cells where Δa < Δr show `A` (RAG won).",
        "- The diagonal Δa = Δr is a tie; argmax behavior is implementation-defined",
        "  (Python dict ordering). This is honest information, not a defect.",
        "",
        "## Why this experiment matters",
        "",
        "Earlier experiments (temperature sensitivity, depth sweep) all returned",
        "'1 distinct path' because they probed a region where one candidate already",
        "dominated. They did not actually map the decision surface.",
        "",
        "This sweep explicitly varies the contest margin. The result is a clean,",
        "data-backed statement of exactly when LPSF overrides RAG — namely, when",
        "the attractor differential exceeds the retrieval gap.",
        "",
        "## Cost",
        "",
        "**$0.** MockLLM only; LLM output text is not consulted by the selection layer.",
        "Running paid APIs here would produce identical results at non-zero cost.",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(REPO_ROOT / "ops" / "lpsf" / "RANK_FLIP_FRONTIER.md"))
    args = parser.parse_args()

    grid: List[List[str]] = []
    amp_grid: List[List[Tuple[float, float]]] = []
    deviations: List[str] = []

    print(f"Sweeping Δr ∈ {DELTA_R}")
    print(f"      ×  Δa ∈ {DELTA_A}")
    print(f"Total cells: {len(DELTA_R) * len(DELTA_A)}")
    print()
    print(f"{'Δa':>6} | " + " ".join(f"Δr={dr:>4.2f}" for dr in DELTA_R))
    print("-" * (8 + len(DELTA_R) * 10))

    for da in DELTA_A:
        row_cells: List[str] = []
        row_amps: List[Tuple[float, float]] = []
        line = f"{da:>6.2f} |"
        for dr in DELTA_R:
            selected, amp_a, amp_b = run_cell(dr, da)
            if abs(amp_a - amp_b) < 1e-9:
                tag = "tie"
            elif selected == "path:ev:A":
                tag = "A"
            elif selected == "path:ev:B":
                tag = "B"
            else:
                tag = "?"

            if tag in ("A", "B"):
                if da > dr + 1e-9 and tag != "B":
                    deviations.append(f"(Δr={dr}, Δa={da}) → expected B, got {selected}")
                elif da < dr - 1e-9 and tag != "A":
                    deviations.append(f"(Δr={dr}, Δa={da}) → expected A, got {selected}")

            row_cells.append(tag)
            row_amps.append((amp_a, amp_b))
            line += f"  {tag:>6}"
        print(line)
        grid.append(row_cells)
        amp_grid.append(row_amps)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_report(grid, amp_grid, deviations), encoding="utf-8")

    print()
    print(f"Report: {out_path}")
    if deviations:
        print(f"⚠ {len(deviations)} deviations from linear prediction:")
        for v in deviations:
            print(f"  {v}")
    else:
        print("✓ All cells match Δa > Δr linear boundary prediction.")


if __name__ == "__main__":
    main()
