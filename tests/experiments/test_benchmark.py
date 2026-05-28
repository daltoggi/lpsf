"""Benchmark orchestrator tests using MockLLM (no API cost)."""

import pytest

from lpsf.experiments.benchmark import BenchmarkReport, run_benchmark
from lpsf.experiments.cost import BudgetExceeded, TokenUsage
from lpsf.experiments.mock_llm import MockLLM


def test_run_benchmark_with_mock_llm():
    llm = MockLLM(seed=0)
    # MockLLM has no .usage by default; attach one for the orchestrator
    llm.usage = TokenUsage(model=llm.version())
    report = run_benchmark(
        llms=[("mock", llm)],
        hypotheses=["H1_before_after", "H5_tension_register"],
        seeds=(0, 1),
        baselines=("LLMOnly", "LLMPlusLPSF"),
        budget_usd=1.0,
        progress=False,
    )
    assert isinstance(report, BenchmarkReport)
    assert len(report.results) == 4  # 2 hypotheses × 2 seeds
    # All mock runs should pass (mock is deterministic and aligned with scenarios)
    assert all(r.passed for r in report.results), [
        (r.hypothesis, r.seed, r.failures) for r in report.results
    ]


def test_run_benchmark_passes_correctly():
    llm = MockLLM(seed=0)
    llm.usage = TokenUsage(model=llm.version())
    report = run_benchmark(
        llms=[("mock", llm)],
        hypotheses=["H1_before_after"],
        seeds=(0,),
        baselines=("LLMOnly", "LLMPlusLPSF"),
        budget_usd=1.0,
        progress=False,
    )
    assert report.passed_count("mock") == 1
    assert report.failed_count("mock") == 0


def test_budget_guard_aborts():
    """If a fake LLM reports too many tokens, BudgetGuard must stop the loop."""
    class ExpensiveLLM:
        def __init__(self):
            self.usage = TokenUsage(model="claude-opus-4-7")
            # Pre-load huge token cost
            self.usage.add(input_tokens=10_000_000, output_tokens=10_000_000)

        def version(self):
            return "claude-opus-4-7"

        def complete(self, prompt, *, context=None):
            return {"response": "x", "confidence": 0.5, "evidence_refs": [], "model": self.version()}

    llm = ExpensiveLLM()
    with pytest.raises(BudgetExceeded):
        run_benchmark(
            llms=[("expensive", llm)],
            hypotheses=["H1_before_after"],
            seeds=(0,),
            baselines=("LLMOnly",),
            budget_usd=0.50,  # Way under projected $900
            progress=False,
        )


def test_by_hypothesis_grouping():
    llm = MockLLM(seed=0)
    llm.usage = TokenUsage(model=llm.version())
    report = run_benchmark(
        llms=[("mock", llm)],
        hypotheses=["H1_before_after", "H5_tension_register"],
        seeds=(0, 1, 2),
        baselines=("LLMOnly", "LLMPlusLPSF"),
        budget_usd=1.0,
        progress=False,
    )
    by_hyp = report.by_hypothesis()
    assert set(by_hyp.keys()) == {"H1_before_after", "H5_tension_register"}
    assert len(by_hyp["H1_before_after"]) == 3
    assert len(by_hyp["H5_tension_register"]) == 3
