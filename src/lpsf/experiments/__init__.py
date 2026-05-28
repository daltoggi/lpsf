"""Public API for the M4 Phase 1 experiment harness.

Mock-only. No network, no real LLM, no catalog-engine.
"""

from .baselines import (
    LLMOnly,
    LLMPlusLPSF,
    LLMPlusLPSFRerank,
    LLMPlusRAG,
    LLMPlusStaticMemory,
    Response,
    baseline_names,
    get_baseline,
)
from .codex_llm import CodexLLM
from .cost import PRICING, BudgetExceeded, BudgetGuard, TokenUsage, summarize
from .mock_llm import MockLLM
from .mock_rag import MockRAG
from .runner import run_experiment, run_query
from .scoring import (
    attractor_alignment,
    evidence_grounding,
    relevance,
    score_response,
    sensitivity_compliance,
)


def _lazy_claude_llm():
    from .claude_llm import ClaudeLLM
    return ClaudeLLM


def _lazy_openai_llm():
    from .openai_llm import OpenAILLM
    return OpenAILLM


def _lazy_benchmark():
    from .benchmark import BenchmarkReport, BenchmarkResult, run_benchmark
    return BenchmarkReport, BenchmarkResult, run_benchmark


def _lazy_report():
    from .report import render_report, report_to_json, write_report
    return render_report, report_to_json, write_report


__all__ = [
    "MockLLM",
    "MockRAG",
    "CodexLLM",
    "Response",
    "LLMOnly",
    "LLMPlusRAG",
    "LLMPlusStaticMemory",
    "LLMPlusLPSF",
    "LLMPlusLPSFRerank",
    "get_baseline",
    "baseline_names",
    "run_query",
    "run_experiment",
    "relevance",
    "evidence_grounding",
    "attractor_alignment",
    "sensitivity_compliance",
    "score_response",
    "PRICING",
    "TokenUsage",
    "BudgetGuard",
    "BudgetExceeded",
    "summarize",
]
