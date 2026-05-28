"""Benchmark orchestrator for M4 Phase 3.

Runs the H1-H5 hypothesis suite across multiple LLMs and seeds, accumulates
token usage, enforces a budget cap, and returns structured results suitable
for the report generator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from lpsf import db

from .cost import BudgetExceeded, BudgetGuard, TokenUsage, summarize
from .hypotheses import HYPOTHESES
from .mock_rag import MockRAG
from .runner import run_experiment
from .scenarios import (
    default_rag_fixture,
    insert_synthetic_event,
    insert_synthetic_snapshot,
)


@dataclass
class BenchmarkResult:
    llm_name: str
    hypothesis: str
    seed: int
    passed: bool
    failures: List[str]
    selected_paths_by_phase: Dict[str, Dict[str, str]]  # phase -> baseline -> path
    score_summary: Dict[str, Any]
    wall_time_seconds: float
    run_id: str


@dataclass
class BenchmarkReport:
    results: List[BenchmarkResult] = field(default_factory=list)
    usages: List[TokenUsage] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def total_wall_time(self) -> float:
        return self.finished_at - self.started_at

    def passed_count(self, llm_name: Optional[str] = None) -> int:
        items = self.results
        if llm_name is not None:
            items = [r for r in items if r.llm_name == llm_name]
        return sum(1 for r in items if r.passed)

    def failed_count(self, llm_name: Optional[str] = None) -> int:
        items = self.results
        if llm_name is not None:
            items = [r for r in items if r.llm_name == llm_name]
        return sum(1 for r in items if not r.passed)

    def by_hypothesis(self) -> Dict[str, List[BenchmarkResult]]:
        out: Dict[str, List[BenchmarkResult]] = {}
        for r in self.results:
            out.setdefault(r.hypothesis, []).append(r)
        return out

    def cost_summary(self) -> Dict[str, Any]:
        return summarize(self.usages)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BenchmarkReport":
        """Reconstruct a BenchmarkReport from report_to_json output.

        Used by scripts/regenerate_report.py so the markdown can be
        re-rendered (e.g. after a render_report() change) without
        re-running the LLM matrix.
        """
        results = [
            BenchmarkResult(
                llm_name=r["llm_name"],
                hypothesis=r["hypothesis"],
                seed=r["seed"],
                passed=r["passed"],
                failures=list(r.get("failures", [])),
                selected_paths_by_phase=r.get("selected_paths_by_phase", {}),
                score_summary=r.get("score_summary", {}),
                wall_time_seconds=r.get("wall_time_seconds", 0.0),
                run_id=r.get("run_id", ""),
            )
            for r in payload.get("results", [])
        ]
        usages: List[TokenUsage] = []
        for entry in payload.get("cost_summary", {}).get("per_model", []):
            u = TokenUsage(
                model=entry["model"],
                input_tokens=int(entry.get("input_tokens", 0)),
                output_tokens=int(entry.get("output_tokens", 0)),
                cached_input_tokens=int(entry.get("cached_input_tokens", 0)),
                calls=int(entry.get("calls", 0)),
                cache_hits=int(entry.get("cache_hits", 0)),
            )
            usages.append(u)
        # total_wall_time is reconstructed by setting started_at=0 and
        # finished_at=wall. The absolute timestamps are not preserved by
        # the JSON dump.
        wall = float(payload.get("total_wall_time", 0.0))
        return cls(
            results=results,
            usages=usages,
            config=dict(payload.get("config", {})),
            started_at=0.0,
            finished_at=wall,
        )


def run_benchmark(
    *,
    llms: Sequence[Tuple[str, Any]],
    hypotheses: Sequence[str] = ("H1_before_after", "H3_privacy_safety", "H4_snapshot_reproducibility", "H5_tension_register"),
    seeds: Sequence[int] = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    baselines: Sequence[str] = ("LLMOnly", "LLMPlusRAG", "LLMPlusLPSF"),
    budget_usd: float = 5.0,
    progress: bool = True,
) -> BenchmarkReport:
    """Run the benchmark matrix.

    llms: list of (display_name, llm_instance). Each must expose .usage
          (TokenUsage) and .stats(). MockLLM is accepted (usage is synthetic).
    hypotheses: which H1-H5 to run. H2 is omitted by default because it's a
                DB-only check and adds no value with real LLMs.
    seeds: independent seeds per (llm, hypothesis). 10 seeds is "standard".
    baselines: which baselines to evaluate per query.
    budget_usd: hard cap. If projected spend exceeds this with safety margin,
                BudgetExceeded is raised and the run stops cleanly.
    """
    guard = BudgetGuard(cap_usd=budget_usd)
    report = BenchmarkReport(
        config={
            "llms": [name for name, _ in llms],
            "hypotheses": list(hypotheses),
            "seeds": list(seeds),
            "baselines": list(baselines),
            "budget_usd": budget_usd,
        },
        started_at=time.time(),
    )

    # Track per-LLM usage objects
    for _, llm in llms:
        u = getattr(llm, "usage", None)
        if isinstance(u, TokenUsage):
            report.usages.append(u)

    total_runs = len(llms) * len(hypotheses) * len(seeds)
    completed = 0

    for llm_name, llm in llms:
        for hyp_name in hypotheses:
            if hyp_name not in HYPOTHESES:
                continue
            hyp_mod = HYPOTHESES[hyp_name]
            for seed in seeds:
                guard.check(report.usages)

                conn = db.init_db(":memory:")
                try:
                    snapshot_id = insert_synthetic_snapshot(
                        conn, snapshot_id=f"snap_bench_{llm_name}_{hyp_name}_{seed}"
                    )
                    event_id = insert_synthetic_event(
                        conn,
                        snapshot_id=snapshot_id,
                        event_id=f"evt_{llm_name}_{hyp_name}_{seed}",
                    )

                    # Some hypotheses embed a custom RAG fixture in their
                    # scenario dict via the "_rag_fixture" key (H6, H3).
                    # Fall back to the default fixture otherwise.
                    scenario = hyp_mod.build_scenario(snapshot_id, event_id)
                    embedded = scenario.pop("_rag_fixture", None)
                    if embedded is not None:
                        fixture = embedded
                    elif hyp_name == "H3_privacy_safety":
                        from .hypotheses.h3_privacy_safety import build_rag_fixture
                        fixture = build_rag_fixture()
                    else:
                        fixture = default_rag_fixture()
                    rag = MockRAG(snapshot_id=snapshot_id, fixture=fixture)

                    start = time.time()
                    result = run_experiment(
                        conn,
                        hypothesis_name=hyp_name,
                        scenario=scenario,
                        baselines=baselines,
                        snapshot_id=snapshot_id,
                        llm=llm,
                        rag=rag,
                        event_id=event_id,
                        seed=seed,
                        verify=hyp_mod.verify,
                    )
                    elapsed = time.time() - start

                    paths_by_phase = {
                        phase: {
                            b: r.selected_path
                            for b, r in by_baseline.items()
                        }
                        for phase, by_baseline in result["phase_results"].items()
                    }
                    bench_result = BenchmarkResult(
                        llm_name=llm_name,
                        hypothesis=hyp_name,
                        seed=seed,
                        passed=result["passed"],
                        failures=[
                            f.get("detail", str(f)) for f in result["failures"]
                        ],
                        selected_paths_by_phase=paths_by_phase,
                        score_summary=result["score_summary"],
                        wall_time_seconds=round(elapsed, 4),
                        run_id=result["run_id"],
                    )
                    report.results.append(bench_result)
                finally:
                    conn.close()

                completed += 1
                if progress:
                    cost = sum(u.cost() for u in report.usages)
                    print(
                        f"[{completed}/{total_runs}] {llm_name} {hyp_name} seed={seed} "
                        f"pass={bench_result.passed} wall={bench_result.wall_time_seconds}s "
                        f"cumcost=${cost:.4f}"
                    )

    report.finished_at = time.time()
    return report
