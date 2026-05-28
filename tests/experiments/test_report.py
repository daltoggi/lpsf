"""Report rendering tests."""

import json

from lpsf.experiments.benchmark import BenchmarkReport, run_benchmark
from lpsf.experiments.cost import TokenUsage
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.report import (
    NEXT_STEPS,
    SCOPE_OF_CLAIMS,
    SCORING_RUBRIC,
    render_report,
    report_to_json,
    write_report,
)


def _make_report():
    llm = MockLLM(seed=0)
    llm.usage = TokenUsage(model=llm.version())
    return run_benchmark(
        llms=[("mock", llm)],
        hypotheses=["H1_before_after", "H5_tension_register"],
        seeds=(0, 1),
        baselines=("LLMOnly", "LLMPlusLPSF"),
        budget_usd=1.0,
        progress=False,
    )


def test_render_report_returns_markdown():
    report = _make_report()
    md = render_report(report)
    assert "# LPSF Phase 3 Evaluation Report" in md
    assert "## Cost summary" in md
    assert "## Pass-rate matrix" in md
    assert "H1_before_after" in md
    assert "H5_tension_register" in md


def test_report_to_json_round_trips():
    report = _make_report()
    raw = report_to_json(report)
    parsed = json.loads(raw)
    assert "config" in parsed
    assert "cost_summary" in parsed
    assert "results" in parsed
    assert len(parsed["results"]) == 4  # 2 hyp × 2 seeds


def test_write_report_to_disk(tmp_path):
    report = _make_report()
    out = tmp_path / "REPORT.md"
    written = write_report(report, str(out))
    assert written == str(out)
    text = out.read_text(encoding="utf-8")
    assert "# LPSF Phase 3 Evaluation Report" in text


def test_failures_section_when_no_failures():
    report = _make_report()
    md = render_report(report)
    assert "All runs passed" in md or "Failure detail" in md


def test_render_report_contains_m5_sections():
    md = render_report(_make_report())
    assert "## Prompts" in md
    assert "System prompt" in md
    assert "## Scoring rubric" in md
    for entry in SCORING_RUBRIC:
        assert f"`{entry['name']}`" in md
    assert "## Next steps" in md
    assert NEXT_STEPS[0][:40] in md


def test_render_report_contains_scope_of_claims():
    md = render_report(_make_report())
    assert "## Scope of claims" in md
    assert "Proven" in md
    assert "NOT yet proven" in md
    # Each proven/not-proven entry's name must appear
    for name, _ in SCOPE_OF_CLAIMS["proven"]:
        assert name in md, f"missing proven claim: {name}"
    for name, _ in SCOPE_OF_CLAIMS["not_yet_proven"]:
        assert name in md, f"missing limitation: {name}"
    # The selection equation must be cited
    assert "argmax(r(c) + a(c))" in md or "argmax(r + a)" in md


def test_from_dict_roundtrip_preserves_results_and_cost():
    original = _make_report()
    payload = json.loads(report_to_json(original))
    rebuilt = BenchmarkReport.from_dict(payload)
    assert len(rebuilt.results) == len(original.results)
    assert rebuilt.config == original.config
    assert rebuilt.cost_summary()["total_calls"] == original.cost_summary()["total_calls"]
    md_original = render_report(original)
    md_rebuilt = render_report(rebuilt)
    # Headings, tables and section names must be identical even though
    # wall-time timestamps don't survive the JSON dump.
    for marker in (
        "## Cost summary",
        "## Pass-rate matrix",
        "## Prompts",
        "## Scoring rubric",
        "## Next steps",
    ):
        assert marker in md_rebuilt
        assert marker in md_original
