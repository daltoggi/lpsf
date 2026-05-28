"""EVALUATION_REPORT.md generator for M4 Phase 3.

Takes a BenchmarkReport and renders a human-readable markdown report:
- run config + budget
- pass rate per (model, hypothesis)
- variance across seeds
- cost breakdown
- selected_path divergence between baselines (qualitative findings)
"""

from __future__ import annotations

import datetime
import json
from collections import defaultdict
from typing import Any, Dict, List

from .benchmark import BenchmarkReport, BenchmarkResult
from .prompts import DEFAULT_SYSTEM_PROMPT as SHARED_SYSTEM_PROMPT


SCORING_RUBRIC = [
    {
        "name": "relevance",
        "range": "[0.0, 1.0]",
        "formula": "matched_keywords / total_expected_keywords",
        "why": "Did the response touch the topics we expected? Measured over selected_path + evidence_refs.",
    },
    {
        "name": "evidence_grounding",
        "range": "[0.0, 1.0]",
        "formula": "in_snapshot_refs / total_evidence_refs",
        "why": "Detects hallucinated citations or refs that escape the pinned snapshot.",
    },
    {
        "name": "attractor_alignment",
        "range": "[0.0, 1.0]",
        "formula": "1.0 if selected_path in active_attractors else |overlap| / |active_attractors|",
        "why": "Validates that the plasticity layer actually shaped path selection.",
    },
    {
        "name": "sensitivity_compliance",
        "range": "{0, 1}",
        "formula": "0 if any forbidden_pattern appears in any serialized response field, else 1",
        "why": "Privacy gate. A single leak fails the run (used by H3).",
    },
]


NEXT_STEPS = [
    "Map the rank-flip frontier: sweep retrieval gap Δr × attractor differential Δa "
    "and chart where LPSF flips the RAG winner. Highest info-per-dollar experiment.",
    "Reconsolidation test (H7): show that a previously deepened bias can be reversed "
    "by counter-experience, not just stacked. Required to justify the 'plasticity' name.",
    "LLM-as-reranker: introduce s(c) = α·r(c) + β·ℓ(c) + γ·a(c) where ℓ(c) comes from "
    "LLM pairwise ranking. Only then does LLM temperature actually affect path selection.",
    "Add a real RAG adapter (read-only over an external knowledge snapshot) "
    "behind the MockRAG Protocol to remove the synthetic-fixture caveat.",
    "Wire EVALUATION_REPORT.json into CI: fail the build if pass-rate drops or "
    "cost-per-run regresses beyond a threshold.",
]


SCOPE_OF_CLAIMS = {
    "proven": [
        ("Controllability", "LPSF attractor can override RAG rankings (H6 adversarial: 10/10 across seeds, baselines diverge consistently)."),
        ("Reproducibility", "Same (snapshot, seed) → same selected_path across independent runs (H4)."),
        ("Baseline independence", "LLMPlusRAG ignores LPSF state by design and selects by RAG score alone (verified empirically by H6 divergence)."),
        ("Harness reliability", "Deterministic, file-cached, no eager SDK imports; re-renders cost $0."),
    ],
    "not_yet_proven": [
        ("LLM internal plasticity", "Path selection is decoupled from LLM output text. Temperature has zero effect on selection by architecture, not by attractor dominance."),
        ("Real-world generalization", "All fixtures are synthetic. A real RAG adapter against an external corpus is required to remove this caveat."),
        ("Operator diversity", "All 8 operators update the same attractor_depth field via different policies. The diversity is in *how* depth changes, not *what* the system computes."),
        ("Reconsolidation / unlearning", "No experiment yet shows that a deepened bias can be reversed by counter-evidence."),
        ("Correctness benefit", "H6 shows LPSF can override RAG. It does NOT show that override is always (or even usually) the right thing to do."),
    ],
}


def render_report(report: BenchmarkReport) -> str:
    """Render the report as a markdown string."""
    parts: List[str] = []
    parts.append("# LPSF Phase 3 Evaluation Report\n")
    parts.append(
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_\n"
    )
    parts.append("")
    parts.append("## Run configuration\n")
    parts.append(_render_config(report))

    parts.append("\n## Cost summary\n")
    parts.append(_render_cost(report))

    parts.append("\n## Pass-rate matrix\n")
    parts.append(_render_pass_matrix(report))

    parts.append("\n## Per-hypothesis findings\n")
    parts.append(_render_per_hypothesis(report))

    parts.append("\n## Prompts\n")
    parts.append(_render_prompts(report))

    parts.append("\n## Scoring rubric\n")
    parts.append(_render_scoring_rubric())

    parts.append("\n## Failure detail\n")
    parts.append(_render_failures(report))

    parts.append("\n## Reproducibility (H4) detail\n")
    parts.append(_render_h4_reproducibility(report))

    parts.append("\n## Scope of claims (read before quoting any number)\n")
    parts.append(_render_scope_of_claims())

    parts.append("\n## Next steps\n")
    parts.append(_render_next_steps())

    parts.append("\n---")
    parts.append(
        "\n_This report is auto-generated by `lpsf.experiments.report.render_report`. "
        "All evidence and prompts used during the runs are stored in the "
        "in-memory SQLite databases of each individual run; they are not "
        "exfiltrated to this report. Token usage and cost figures reflect "
        "PRICING in `lpsf.experiments.cost.PRICING` at the time of run._\n"
    )
    return "\n".join(parts)


def write_report(report: BenchmarkReport, output_path: str) -> str:
    """Render and write the report to disk. Returns the written path."""
    text = render_report(report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path


# ---------- section renderers --------------------------------------------

def _render_config(report: BenchmarkReport) -> str:
    cfg = report.config
    lines = [
        f"- **LLMs:** {', '.join(cfg.get('llms', []))}",
        f"- **Hypotheses:** {', '.join(cfg.get('hypotheses', []))}",
        f"- **Seeds:** {len(cfg.get('seeds', []))} per (llm × hypothesis)",
        f"- **Baselines:** {', '.join(cfg.get('baselines', []))}",
        f"- **Budget cap:** ${cfg.get('budget_usd', 0):.2f}",
        f"- **Total runs:** {len(report.results)}",
        f"- **Wall time:** {report.total_wall_time:.1f}s",
    ]
    return "\n".join(lines)


def _render_cost(report: BenchmarkReport) -> str:
    summary = report.cost_summary()
    lines = ["| Model | Calls | Cache hits | Input tok | Output tok | Cached tok | Cost (USD) |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for entry in summary["per_model"]:
        lines.append(
            "| {model} | {calls} | {cache_hits} | {input_tokens} | "
            "{output_tokens} | {cached_input_tokens} | ${estimated_cost_usd:.4f} |".format(
                **entry
            )
        )
    lines.append(
        f"| **TOTAL** | **{summary['total_calls']}** | "
        f"**{summary['total_cache_hits']}** | — | — | — | "
        f"**${summary['total_estimated_cost_usd']:.4f}** |"
    )
    return "\n".join(lines)


def _render_pass_matrix(report: BenchmarkReport) -> str:
    # rows = hypothesis, cols = model, cell = passed/total
    by_hyp = report.by_hypothesis()
    models = list(report.config.get("llms", []))
    lines = ["| Hypothesis | " + " | ".join(models) + " |",
             "|---|" + "|".join(["---:"] * len(models)) + "|"]
    for hyp_name, results in by_hyp.items():
        row = [hyp_name]
        for model in models:
            subset = [r for r in results if r.llm_name == model]
            passed = sum(1 for r in subset if r.passed)
            total = len(subset)
            pct = (passed / total * 100) if total else 0
            row.append(f"{passed}/{total} ({pct:.0f}%)")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _render_per_hypothesis(report: BenchmarkReport) -> str:
    by_hyp = report.by_hypothesis()
    parts: List[str] = []
    for hyp_name, results in by_hyp.items():
        parts.append(f"### {hyp_name}")
        parts.append("")
        # Average wall time
        avg_wall = sum(r.wall_time_seconds for r in results) / max(len(results), 1)
        parts.append(f"- Runs: {len(results)}, avg wall: {avg_wall:.2f}s")
        # Selected paths by model
        paths_by_model: Dict[str, List[str]] = defaultdict(list)
        for r in results:
            for phase, by_baseline in r.selected_paths_by_phase.items():
                if "LLMPlusLPSF" in by_baseline:
                    paths_by_model[r.llm_name].append(by_baseline["LLMPlusLPSF"])
        for model, paths in paths_by_model.items():
            unique = sorted(set(paths))
            parts.append(
                f"- {model} LLMPlusLPSF selected_paths: {len(unique)} unique "
                f"across {len(paths)} (phase, seed) cells"
            )
            if unique:
                parts.append(f"  - Examples: {unique[:3]}")
        parts.append("")
    return "\n".join(parts)


def _render_prompts(report: BenchmarkReport) -> str:
    """Document the system prompt and the user-prompt schema used in this run."""
    lines: List[str] = [
        "Both the Claude and OpenAI wrappers share the same evidence-grounded "
        "selector system prompt (see `lpsf.experiments.prompts`). The user "
        "prompt is built from `query` + a list of `{id, sanitized_summary}` "
        "evidence rows; raw bodies are never read.",
        "",
        "**System prompt** (shared, temperature=0):",
        "",
        "```",
        SHARED_SYSTEM_PROMPT,
        "```",
        "",
        "**User prompt schema** (from `lpsf.experiments.baselines._build_prompt`):",
        "",
        "```",
        "Query: <query>",
        "Evidence:",
        "- <evidence_id>: <sanitized_summary>",
        "- ...",
        "```",
    ]
    return "\n".join(lines)


def _render_scoring_rubric() -> str:
    """Document the four scorers from lpsf.experiments.scoring."""
    lines = [
        "Every baseline response is scored on four orthogonal axes (see "
        "`lpsf.experiments.scoring`):",
        "",
        "| Scorer | Range | Formula | Why |",
        "|---|---|---|---|",
    ]
    for entry in SCORING_RUBRIC:
        lines.append(
            "| `{name}` | {range} | {formula} | {why} |".format(**entry)
        )
    lines.append("")
    lines.append(
        "Hypothesis pass/fail logic combines these scores per the hypothesis "
        "module (`lpsf.experiments.hypotheses.H{1,2,3,4,5}.verify`)."
    )
    return "\n".join(lines)


def _render_next_steps() -> str:
    """Standing next-steps backlog. Updated as runs reveal new gaps."""
    return "\n".join(f"- {item}" for item in NEXT_STEPS)


def _render_scope_of_claims() -> str:
    """Explicit scope statement. Prevents over-reading the pass-rate matrix."""
    lines = [
        "This benchmark validates that the LPSF harness behaves consistently with "
        "its own specification. It does NOT, on its own, prove the broader LPSF "
        "research thesis. The honest scope is:",
        "",
        "### Proven (controllability, reproducibility, mechanism)",
        "",
    ]
    for name, detail in SCOPE_OF_CLAIMS["proven"]:
        lines.append(f"- **{name}** — {detail}")
    lines += [
        "",
        "### NOT yet proven (do not quote these as established)",
        "",
    ]
    for name, detail in SCOPE_OF_CLAIMS["not_yet_proven"]:
        lines.append(f"- **{name}** — {detail}")
    lines += [
        "",
        "See `docs/lpsf/CURRENT_STATUS.md` for the canonical positioning. "
        "The selection mechanism collapses to `c* = argmax(r(c) + a(c))`, where "
        "LLM output text plays no role in choosing the path — only in the response "
        "field that is logged. Read every number on this report through that lens.",
    ]
    return "\n".join(lines)


def _render_failures(report: BenchmarkReport) -> str:
    failed = [r for r in report.results if not r.passed]
    if not failed:
        return "_All runs passed._"
    lines = ["| LLM | Hypothesis | Seed | Failure |", "|---|---|---:|---|"]
    for r in failed:
        detail = "; ".join(r.failures)[:200] or "(no detail)"
        lines.append(f"| {r.llm_name} | {r.hypothesis} | {r.seed} | {detail} |")
    return "\n".join(lines)


def _render_h4_reproducibility(report: BenchmarkReport) -> str:
    """For H4, group by model + seed and check selected_path consistency."""
    h4 = [r for r in report.results if r.hypothesis == "H4_snapshot_reproducibility"]
    if not h4:
        return "_H4 not in this run._"
    lines = ["| Model | Seeds covered | Distinct paths (LLMPlusLPSF) |", "|---|---:|---:|"]
    by_model: Dict[str, List[BenchmarkResult]] = defaultdict(list)
    for r in h4:
        by_model[r.llm_name].append(r)
    for model, runs in by_model.items():
        paths = []
        for r in runs:
            for phase, by_baseline in r.selected_paths_by_phase.items():
                if "LLMPlusLPSF" in by_baseline:
                    paths.append(by_baseline["LLMPlusLPSF"])
        unique = sorted(set(paths))
        lines.append(f"| {model} | {len(runs)} | {len(unique)} |")
    lines.append("")
    lines.append(
        "_distinct_paths = 1 across all seeds reflects an architectural property: "
        "in LLMPlusLPSF, `selected = argmax(rag_score + attractor_depth)` and the LLM "
        "output text is not an input to this argmax. Reproducibility here is therefore "
        "expected, not surprising. See `docs/lpsf/CURRENT_STATUS.md` for full positioning._"
    )
    return "\n".join(lines)


# ---------- helper -------------------------------------------------------

def report_to_json(report: BenchmarkReport) -> str:
    """Dump a machine-readable JSON of the report (for cross-tool reuse)."""
    payload = {
        "config": report.config,
        "cost_summary": report.cost_summary(),
        "total_wall_time": report.total_wall_time,
        "results": [
            {
                "llm_name": r.llm_name,
                "hypothesis": r.hypothesis,
                "seed": r.seed,
                "passed": r.passed,
                "failures": r.failures,
                "selected_paths_by_phase": r.selected_paths_by_phase,
                "score_summary": r.score_summary,
                "wall_time_seconds": r.wall_time_seconds,
                "run_id": r.run_id,
            }
            for r in report.results
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
