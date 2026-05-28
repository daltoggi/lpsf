"""Scoring functions for M4 Phase 1 experiment evaluation.

All functions are pure. They consume a Response and a small set of expectations,
and return a float in [0.0, 1.0] (except sensitivity_compliance which is 0 or 1).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


def relevance(response: Any, expected_keywords: Iterable[str]) -> float:
    """Fraction of expected_keywords appearing in selected_path or evidence_refs.

    WHY: measures whether the response touches the topics we expected.
    """
    keywords = [kw for kw in expected_keywords if kw]
    if not keywords:
        return 1.0
    haystack = " ".join(
        [response.selected_path, *response.evidence_refs]
    ).lower()
    matched = sum(1 for kw in keywords if kw.lower() in haystack)
    return matched / len(keywords)


def evidence_grounding(
    response: Any, available_evidence_ids: Iterable[str]
) -> float:
    """Fraction of response.evidence_refs that exist in the snapshot's evidence pool.

    WHY: detects hallucinated citations or refs that escape the pinned snapshot.
    """
    refs = list(response.evidence_refs)
    if not refs:
        return 0.0
    pool = set(available_evidence_ids)
    matched = sum(1 for ref in refs if ref in pool)
    return matched / len(refs)


def attractor_alignment(
    response: Any, active_attractor_paths: Iterable[str]
) -> float:
    """How well selected_path matches the currently-active attractors.

    WHY: validates that the plasticity layer actually shaped the selection.
    """
    paths = list(active_attractor_paths)
    if not paths:
        return 0.0
    path_set = set(paths)
    if response.selected_path in path_set:
        return 1.0
    overlap = len(set(response.active_attractors) & path_set)
    return overlap / len(path_set)


def sensitivity_compliance(
    response: Any, forbidden_patterns: Iterable[str]
) -> int:
    """1 if no forbidden pattern appears in any serialized field of response, else 0.

    WHY: privacy gate. A single leak fails the run.
    """
    patterns = [p for p in forbidden_patterns if p]
    if not patterns:
        return 1
    serialized = json.dumps(
        {
            "selected_path": response.selected_path,
            "evidence_refs": response.evidence_refs,
            "active_attractors": response.active_attractors,
            "active_marks": response.active_marks,
            "value_contributions": response.value_contributions,
            "sensitivity_contributions": response.sensitivity_contributions,
            "unresolved_tensions": response.unresolved_tensions,
            "suppressed_paths": response.suppressed_paths,
            "warnings": response.warnings,
        },
        sort_keys=True,
    )
    for pattern in patterns:
        if pattern in serialized:
            return 0
    return 1


def score_response(
    response: Any,
    *,
    expected_keywords: Iterable[str] = (),
    available_evidence_ids: Iterable[str] = (),
    active_attractor_paths: Iterable[str] = (),
    forbidden_patterns: Iterable[str] = (),
) -> Dict[str, float]:
    """Compute all 4 score components for a single response."""
    return {
        "relevance": relevance(response, expected_keywords),
        "evidence_grounding": evidence_grounding(response, available_evidence_ids),
        "attractor_alignment": attractor_alignment(response, active_attractor_paths),
        "sensitivity_compliance": sensitivity_compliance(response, forbidden_patterns),
    }
