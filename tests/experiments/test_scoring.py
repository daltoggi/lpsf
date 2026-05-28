"""Tests for scoring functions."""

from lpsf.experiments.baselines import Response
from lpsf.experiments.scoring import (
    attractor_alignment,
    evidence_grounding,
    relevance,
    score_response,
    sensitivity_compliance,
)


def _resp(**overrides):
    base = dict(
        selected_path="path:ev:A",
        evidence_refs=["ev:A"],
        active_attractors=["path:ev:A"],
        active_marks=["mark_1"],
        value_contributions={},
        sensitivity_contributions={},
        unresolved_tensions=[],
        suppressed_paths=[],
        warnings=[],
        score_components={},
        baseline_name="test",
        model_version="mock-llm-v0",
    )
    base.update(overrides)
    return Response(**base)


def test_relevance_full_match():
    r = _resp(selected_path="path:ev:A", evidence_refs=["best"])
    assert relevance(r, ["best", "path"]) == 1.0


def test_relevance_partial():
    r = _resp(selected_path="path:ev:A", evidence_refs=[])
    assert relevance(r, ["path", "missing"]) == 0.5


def test_relevance_no_expected_returns_one():
    assert relevance(_resp(), []) == 1.0


def test_evidence_grounding_all_present():
    r = _resp(evidence_refs=["ev:A", "ev:B"])
    assert evidence_grounding(r, ["ev:A", "ev:B", "ev:C"]) == 1.0


def test_evidence_grounding_partial():
    r = _resp(evidence_refs=["ev:A", "ev:Z"])
    assert evidence_grounding(r, ["ev:A"]) == 0.5


def test_evidence_grounding_empty_refs():
    r = _resp(evidence_refs=[])
    assert evidence_grounding(r, ["ev:A"]) == 0.0


def test_attractor_alignment_exact():
    r = _resp(selected_path="path:ev:A", active_attractors=["path:ev:A"])
    assert attractor_alignment(r, ["path:ev:A"]) == 1.0


def test_attractor_alignment_overlap():
    r = _resp(selected_path="path:other", active_attractors=["path:ev:A", "path:ev:B"])
    assert attractor_alignment(r, ["path:ev:A", "path:ev:B"]) == 1.0


def test_attractor_alignment_empty_paths():
    assert attractor_alignment(_resp(), []) == 0.0


def test_sensitivity_compliance_clean():
    r = _resp(selected_path="path:ev:A", evidence_refs=["ev:A"])
    assert sensitivity_compliance(r, ["FORBIDDEN_TOKEN"]) == 1


def test_sensitivity_compliance_leak_detected():
    r = _resp(warnings=["leaked FORBIDDEN_TOKEN_42"])
    assert sensitivity_compliance(r, ["FORBIDDEN_TOKEN_42"]) == 0


def test_score_response_all_components():
    r = _resp()
    out = score_response(
        r,
        expected_keywords=["path"],
        available_evidence_ids=["ev:A"],
        active_attractor_paths=["path:ev:A"],
        forbidden_patterns=[],
    )
    assert set(out) == {
        "relevance",
        "evidence_grounding",
        "attractor_alignment",
        "sensitivity_compliance",
    }
