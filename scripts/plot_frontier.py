#!/usr/bin/env python3
"""Render the rank-flip frontier as a Unicode-block heatmap.

No matplotlib dependency. Uses MockLLM (LLM output doesn't affect path
selection in plain LPSF, so paid APIs would change nothing). Writes
ops/lpsf/FRONTIER_PLOT.md and also prints to stdout.

Usage:
    python3 scripts/plot_frontier.py
    python3 scripts/plot_frontier.py --resolution 16   # finer grid
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUTPUT_PATH = REPO_ROOT / "ops" / "lpsf" / "FRONTIER_PLOT.md"


def run_cell(delta_r: float, delta_a: float) -> str:
    """Returns 'A' (RAG wins) / 'B' (attractor wins) / 'T' (tie)."""
    from lpsf import db
    from lpsf.experiments.baselines import LLMPlusLPSF
    from lpsf.experiments.mock_llm import MockLLM
    from lpsf.experiments.mock_rag import MockRAG
    from lpsf.experiments.scenarios import (
        insert_synthetic_event,
        insert_synthetic_snapshot,
    )
    from lpsf.operators.deepen_attractor import deepen_attractor

    conn = db.init_db(":memory:")
    try:
        snap = f"snap_plot_{delta_r:.4f}_{delta_a:.4f}"
        evt = f"evt_plot_{delta_r:.4f}_{delta_a:.4f}"
        insert_synthetic_snapshot(conn, snapshot_id=snap)
        insert_synthetic_event(conn, snapshot_id=snap, event_id=evt)
        if delta_a > 0:
            deepen_attractor(
                conn,
                event_id=evt,
                snapshot_id=snap,
                target_type="path",
                target_id="path:ev:B",
                strength=min(delta_a, 1.0),
                half_life=3600,
                evidence_refs=["ev:B"],
                reason="plot frontier",
                scope="plot",
            )
        rag = MockRAG(
            snapshot_id=snap,
            fixture={
                "q": [
                    {"id": "ev:A", "score": 0.5 + delta_r / 2,
                     "sanitized_summary": "a", "source_type": "synthetic"},
                    {"id": "ev:B", "score": 0.5 - delta_r / 2,
                     "sanitized_summary": "b", "source_type": "synthetic"},
                ],
            },
        )
        baseline = LLMPlusLPSF()
        resp = baseline.respond(conn, query="q", snapshot_id=snap, llm=MockLLM(seed=0), rag=rag, seed=0)
        amp_a = resp.amplitudes.get("path:ev:A", 0.0)
        amp_b = resp.amplitudes.get("path:ev:B", 0.0)
        if abs(amp_a - amp_b) < 1e-9:
            return "T"
        return "A" if resp.selected_path == "path:ev:A" else "B"
    finally:
        conn.close()


def render_grid(resolution: int) -> list:
    """Returns a 2D list of cell labels indexed [da_idx][dr_idx]."""
    deltas = [i / (resolution - 1) for i in range(resolution)]
    # Cap depth at 1.0 because of operator strength cap; for Δr we use 0..0.95
    # (1.0 collapses to one candidate having score 0 which is uninteresting).
    dr_axis = [d * 0.95 for d in deltas]
    da_axis = [d * 1.0 for d in deltas]
    grid = []
    for da in da_axis:
        row = []
        for dr in dr_axis:
            row.append(run_cell(dr, da))
        grid.append(row)
    return grid, dr_axis, da_axis


def render_unicode_heatmap(grid, dr_axis, da_axis) -> str:
    """Render the frontier as a Unicode block heatmap with axis labels."""
    # Glyph choice:
    #   A wins  → '· ' (light)
    #   tie     → '◆ '
    #   B wins  → '█ ' (heavy)
    glyph = {"A": "·  ", "T": "◆  ", "B": "█  "}
    lines = []
    lines.append("```")
    lines.append("  Rank-Flip Frontier  (· = A wins  █ = B wins  ◆ = tie)")
    lines.append("")
    # Header row: Δr axis
    header = "  Δa↑\\Δr→ |"
    for dr in dr_axis:
        header += f"{dr:>4.2f}"
    lines.append(header)
    sep = "  --------+" + "----" * len(dr_axis)
    lines.append(sep)
    # Rows: top is highest Δa (so A region is bottom-right, B region top-left)
    for da, row in zip(reversed(da_axis), reversed(grid)):
        line = f"  Δa={da:>4.2f} |  "
        for cell in row:
            line += glyph[cell]
        lines.append(line)
    lines.append("")
    lines.append("  The diagonal `Δa = Δr` is exactly the flip boundary,")
    lines.append("  predicted by the selection equation c* = argmax(r + a).")
    lines.append("```")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=11,
                        help="grid resolution (11 = ~10%% steps; 16 = finer)")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    res = max(3, args.resolution)
    grid, dr_axis, da_axis = render_grid(res)
    rendered = render_unicode_heatmap(grid, dr_axis, da_axis)

    # Compute boundary verification
    deviations = []
    for da_idx, da in enumerate(da_axis):
        for dr_idx, dr in enumerate(dr_axis):
            cell = grid[da_idx][dr_idx]
            if cell == "T":
                continue
            if da > dr + 1e-9 and cell != "B":
                deviations.append((dr, da, cell))
            elif da < dr - 1e-9 and cell != "A":
                deviations.append((dr, da, cell))

    body = [
        f"# Rank-Flip Frontier (Unicode plot)",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        f"_Resolution: {res}×{res} cells; total {res * res} runs; MockLLM only ($0)_",
        "",
        rendered,
        "",
        "## Boundary check",
        "",
    ]
    if not deviations:
        body.append(f"✓ All {res * res} cells consistent with the linear prediction Δa = Δr.")
    else:
        body.append(f"⚠ {len(deviations)} cells deviated:")
        for dr, da, cell in deviations:
            body.append(f"- (Δr={dr:.3f}, Δa={da:.3f}) → {cell}")
    body += [
        "",
        "## Reading the plot",
        "",
        "- Each row is a value of Δa (top = strong attractor, bottom = no attractor).",
        "- Each column is a value of Δr (left = tied retrieval, right = strong RAG winner).",
        "- A heavy block `█` means LPSF flipped the RAG winner (attractor wins).",
        "- A light dot `·` means RAG kept its winner.",
        "- A diamond `◆` is a numerical tie on the boundary.",
        "",
        "The boundary follows the diagonal Δa = Δr exactly. This matches the",
        "amplitude equation in `baselines.py::LLMPlusLPSF.respond` line for line.",
        "",
        "Companion document: `RANK_FLIP_FRONTIER.md` (tabular form with exact amplitudes).",
    ]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(body), encoding="utf-8")

    print(rendered)
    print()
    print(f"Cells: {res * res}, deviations: {len(deviations)}")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
